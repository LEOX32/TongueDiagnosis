import os
import tempfile
import torch
import threading
import time
from PIL import Image
import numpy as np
from ultralytics import YOLO
from segment_anything import sam_model_registry,SamPredictor
from application.net.model.resnet import ResNetPredictor
from application.net.model.resnet_improved import ImprovedResNet50, ImprovedResNetPredictor, ImprovedResNetMultiOutputPredictor
from application.net.model.yolo_sam_joint import YOLOv11SAMJointPredictor
from application.net.sparse_sam import SparseSamModel

current_dir = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(current_dir, 'weights')


class TonguePredictor:
    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 yolo_path=os.path.join(BASE_PATH, 'yolov11.pt'),
                 sam_path=os.path.join(BASE_PATH, 'sam_vit_b_01ec64.pth'),
                 resnet_path=[
                     os.path.join(BASE_PATH, 'tongue_color.pth'),
                     os.path.join(BASE_PATH, 'tongue_coat_color.pth'),
                     os.path.join(BASE_PATH, 'thickness.pth'),
                     os.path.join(BASE_PATH, 'rot_and_greasy.pth')
                 ],
                 use_sparse_attention=False,
                 use_improved_resnet=False,
                 improved_resnet_path=os.path.join(current_dir, '..', '..', 'checkpoints', 'improved_resnet', 'full_model', 'best_model.pth'),
                 use_multi_output=True,
                 use_yolo_sam_joint=False,
                 joint_model_path=os.path.join(BASE_PATH, 'best_model.pth')
                 ):
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return

            start_time = time.time()
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"Using device: {device}")

            self.device = device
            self.use_improved_resnet = use_improved_resnet
            self.use_yolo_sam_joint = use_yolo_sam_joint

            if use_yolo_sam_joint:
                print("使用 YOLO-SAM 联合模型...")
                self.yolo_sam_joint = YOLOv11SAMJointPredictor(
                    yolo_path=yolo_path,
                    sam_path=sam_path,
                    joint_model_path=joint_model_path,
                    device=device
                )
                self.yolo = None
                self.sam = None
                self.sam_predictor = None
                self.use_sparse = False
            else:
                print("正在加载 YOLO 模型...")
                self.yolo = YOLO(yolo_path)
                self.yolo.to(device)

                if use_sparse_attention:
                    print("Using Sparse Attention SAM")
                    self.sam = SparseSamModel(model_type="vit_b", checkpoint=sam_path, device=device)
                    self.use_sparse = True
                    self.sam_predictor = None
                else:
                    print("Using Original SAM")
                    self.sam = sam_model_registry["vit_b"](checkpoint=sam_path)
                    self.sam.to(device)
                    self.use_sparse = False
                    self.sam_predictor = SamPredictor(sam_model=self.sam)

                self.yolo_sam_joint = None
            
            print("正在加载 ResNet 模型...")
            if use_improved_resnet:
                if use_multi_output:
                    print("使用改进的 ResNet 多输出模型（4特征联合预测）")
                    self.resnet = ImprovedResNetMultiOutputPredictor(improved_resnet_path, device=device)
                else:
                    print("使用改进的 ResNet 模型（注意力门控 + 多尺度卷积）")
                    self.resnet = ImprovedResNetPredictor(improved_resnet_path, device=device)
            else:
                print("使用原始 ResNet 模型")
                self.resnet = ResNetPredictor(resnet_path, device=device)
            
            TonguePredictor._initialized = True
            load_time = time.time() - start_time
            print(f"所有模型加载完成，耗时：{load_time:.2f}秒")
            
            print("开始预热模型...")
            self._warmup_models()
    
    def _warmup_models(self):
        """预热模型，减少首次预测延迟"""
        try:
            warmup_start = time.time()
            dummy_img = Image.new('RGB', (224, 224), color='red')
            dummy_array = np.array(dummy_img)

            if self.use_yolo_sam_joint:
                print("预热 YOLO-SAM 联合模型...")
                dummy_tensor = torch.from_numpy(dummy_array).permute(2, 0, 1).unsqueeze(0).float().to(self.device) / 255.0
                with torch.no_grad():
                    _ = self.yolo_sam_joint(dummy_tensor)
            else:
                print("预热 YOLO 模型...")
                with torch.no_grad():
                    self.yolo.predict(dummy_img, verbose=False)

                print("预热 SAM 模型...")
                if not self.use_sparse and self.sam_predictor:
                    self.sam_predictor.set_image(dummy_array)

            print("预热 ResNet 模型...")
            self.resnet.predict(dummy_array)

            warmup_time = time.time() - warmup_start
            print(f"模型预热完成，耗时: {warmup_time:.2f}秒")
        except Exception as e:
            print(f"模型预热失败（不影响使用）: {e}")

    def __predict(self, img, record_id, fun, db=None):
        try:
            if isinstance(img, str):
                predict_img = Image.open(img)
            else:
                img.seek(0)
                predict_img = Image.open(img)

            print("Tongue positioning and segmentation")

            if self.use_yolo_sam_joint:
                with torch.no_grad():
                    img_array = np.array(predict_img)
                    img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0).float().to(self.device) / 255.0
                    masks, bboxes = self.yolo_sam_joint(img_tensor)

                if bboxes is None or (isinstance(bboxes, torch.Tensor) and bboxes.sum() == 0):
                    fun(event_id=record_id,
                        tongue_color=None,
                        coating_color=None,
                        tongue_thickness=None,
                        rot_greasy=None,
                        code=201,
                        db=db)
                    print("The picture is not legal and has no tongue.")
                    return

                bbox = bboxes[0].cpu().numpy()
                x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

                mask = masks[0, 0].cpu().numpy()
                original_img = np.array(predict_img)
                pred = original_img * mask[:, :, np.newaxis]
                result = Image.fromarray(pred.astype(np.uint8)).crop((x1, y1, x2, y2)).convert("RGB")
                result = np.array(result)
            else:
                self.yolo.eval()
                with torch.no_grad():
                    results = self.yolo.predict(predict_img, verbose=False)

                if len(results) == 0 or len(results[0].boxes) == 0:
                    fun(event_id=record_id,
                        tongue_color=None,
                        coating_color=None,
                        tongue_thickness=None,
                        rot_greasy=None,
                        code=201,
                        db=db)
                    print("The picture is not legal and has no tongue.")
                    return
                elif len(results[0].boxes) > 1:
                    print(f"Multiple tongues detected, selecting highest confidence...")

                with torch.no_grad():
                    boxes = results[0].boxes.xyxy[0]
                    x1, y1, x2, y2 = boxes[0].item(), boxes[1].item(), boxes[2].item(), boxes[3].item()

                    if self.use_sparse:
                        predictor = self.sam.get_predictor()
                    else:
                        predictor = self.sam_predictor

                    predictor.set_image(np.array(predict_img))
                    masks, _, _ = predictor.predict(box=np.array([x1, y1, x2, y2]))
                    original_img = np.array(predict_img)
                    masks = np.transpose(masks, (1, 2, 0))
                    pred = original_img * masks
                    result = Image.fromarray(pred).crop((x1, y1, x2, y2)).convert("RGB")
                    result = np.array(result)

            result = self.resnet.predict(result)
            print("Tongue analysis")
            predict_result = {
                "code": 0,
                'tongue_color': result[0],
                'tongue_coat_color': result[1],
                'thickness': result[2],
                'rot_and_greasy': result[3]
            }
            fun(event_id=record_id,
                tongue_color=result[0],
                coating_color=result[1],
                tongue_thickness=result[2],
                rot_greasy=result[3],
                code=1,
                db=db)
            return predict_result
        except Exception as e:
            print(f"预测失败: {e}")
            fun(event_id=record_id,
                tongue_color=None,
                coating_color=None,
                tongue_thickness=None,
                rot_greasy=None,
                code=203,
                db=db)

    def predict(self, img, record_id, fun, db=None):
        try:
            if isinstance(img, str):
                self.__predict(img, record_id, fun, db)
                return {"code": 0}
            else:
                try:
                    img.seek(0)
                    content = img.read()
                    if not content or len(content) == 0:
                        print("警告: 文件内容为空")
                        fun(event_id=record_id,
                            tongue_color=None,
                            coating_color=None,
                            tongue_thickness=None,
                            rot_greasy=None,
                            code=203,
                            db=db)
                        return {"code": 3}
                    tmpfile = tempfile.SpooledTemporaryFile()
                    tmpfile.write(content)
                    tmpfile.seek(0)
                    self.__predict(tmpfile, record_id, fun, db)
                    tmpfile.close()
                except Exception as e:
                    print(f"文件处理错误: {e}")
                    fun(event_id=record_id,
                        tongue_color=None,
                        coating_color=None,
                        tongue_thickness=None,
                        rot_greasy=None,
                        code=203,
                        db=db)
                    return {"code": 3}
                finally:
                    try:
                        img.seek(0)
                    except:
                        pass
                return {"code": 0}
        except Exception as e:
            print(f"预测失败: {e}")
            return {"code": 3}
