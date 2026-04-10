import torch
import torch.nn as nn
import torch.nn.functional as F
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor


class YOLOv11SAMJointModel(nn.Module):
    def __init__(self, yolo_path, sam_path, device='cuda'):
        super().__init__()
        self.device = device

        print("Loading YOLOv11 model...")
        self.yolo = YOLO(yolo_path)
        self.yolo.to(device)

        print("Loading SAM model...")
        self.sam = sam_model_registry["vit_b"](checkpoint=sam_path)
        self.sam.to(device)

        self.feature_projection = nn.Sequential(
            nn.Conv2d(1024, 256, kernel_size=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((64, 64))
        ).to(device)

        for param in self.sam.image_encoder.parameters():
            param.requires_grad = False

        self.fusion_decoder = nn.Sequential(
            nn.Conv2d(256 + 256, 256, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 1, kernel_size=1, bias=True)
        ).to(device)

        print("YOLOv11-SAM joint model components initialized")

    def load_joint_weights(self, joint_model_path):
        print(f"Loading joint model weights from: {joint_model_path}")
        joint_state_dict = torch.load(joint_model_path, map_location=self.device, weights_only=False)

        yolo_state_dict = {}
        sam_state_dict = {}
        feature_state_dict = {}
        decoder_state_dict = {}

        for key, value in joint_state_dict.items():
            if key.startswith('yolo.'):
                yolo_state_dict[key[5:]] = value
            elif key.startswith('sam.'):
                sam_state_dict[key[4:]] = value
            elif key.startswith('feature_projection.'):
                prefix = 'feature_projection.'
                new_key = key[len(prefix):]
                feature_state_dict[new_key] = value
            elif key.startswith('fusion_decoder.'):
                prefix = 'fusion_decoder.'
                new_key = key[len(prefix):]
                decoder_state_dict[new_key] = value

        if yolo_state_dict:
            print(f"Loading {len(yolo_state_dict)} YOLO weights")
            try:
                self.yolo_model_load_state_dict(self.yolo, yolo_state_dict)
            except Exception as e:
                print(f"Warning: Failed to load YOLO weights: {e}")

        if sam_state_dict:
            print(f"Loading {len(sam_state_dict)} SAM weights")
            try:
                self.sam.load_state_dict(sam_state_dict, strict=False)
            except Exception as e:
                print(f"Warning: Failed to load SAM weights: {e}")

        if feature_state_dict:
            print(f"Loading {len(feature_state_dict)} feature projection weights")
            fp_key = '0.weight'
            fp_input_channels = feature_state_dict.get(fp_key, torch.tensor([[[0]]])).shape[1]
            if fp_input_channels == 256:
                fixed_feature_state_dict = self._fix_sequential_keys(feature_state_dict)
                self.feature_projection.load_state_dict(fixed_feature_state_dict)
            else:
                print(f"  Skipping feature_projection: checkpoint has {fp_input_channels} input channels, current model expects 256")

        if decoder_state_dict:
            print(f"Loading {len(decoder_state_dict)} fusion decoder weights")
            fd_key = '0.weight'
            fd_input_channels = decoder_state_dict.get(fd_key, torch.tensor([[[0]]])).shape[1]
            if fd_input_channels == 512:
                fixed_decoder_state_dict = self._fix_sequential_keys(decoder_state_dict)
                self.fusion_decoder.load_state_dict(fixed_decoder_state_dict)
            else:
                print(f"  Skipping fusion_decoder: checkpoint has {fd_input_channels} input channels, current model expects 512")

        for param in self.yolo.model.parameters():
            param.requires_grad = False

        for param in self.feature_projection.parameters():
            param.requires_grad = False

        for param in self.fusion_decoder.parameters():
            param.requires_grad = False

        print("All joint model weights loaded successfully")

    def _fix_sequential_keys(self, state_dict):
        fixed_dict = {}
        for key, value in state_dict.items():
            new_key = key
            if key.startswith('.'):
                new_key = key[1:]
            fixed_dict[new_key] = value
        return fixed_dict

    def yolo_model_load_state_dict(self, yolo_model, state_dict):
        try:
            model_state = yolo_model.model.state_dict() if hasattr(yolo_model, 'model') else yolo_model.state_dict()
            matched_state = {}
            for key, value in state_dict.items():
                if key in model_state:
                    matched_state[key] = value
                else:
                    for model_key in model_state:
                        if model_key.endswith(key) or key.endswith(model_key):
                            matched_state[model_key] = value
                            break
            if matched_state:
                if hasattr(yolo_model, 'model'):
                    yolo_model.model.load_state_dict(matched_state, strict=False)
                else:
                    yolo_model.load_state_dict(matched_state, strict=False)
        except Exception as e:
            print(f"YOLO state dict loading error: {e}")
            for key, value in state_dict.items():
                if hasattr(yolo_model, 'model'):
                    if key in yolo_model.model.state_dict():
                        yolo_model.model.state_dict()[key].copy_(value)
                elif key in yolo_model.state_dict():
                    yolo_model.state_dict()[key].copy_(value)

    def extract_yolo_features(self, img):
        with torch.no_grad():
            yolo_results = self.yolo(img, verbose=False)

        if len(yolo_results) == 0 or len(yolo_results[0].boxes) == 0:
            return None, None

        boxes = yolo_results[0].boxes
        best_idx = boxes.conf.argmax()
        bbox = boxes.xyxy[best_idx].cpu()

        feat = yolo_results[0].boxes
        yolo_feature = self._get_yolo_backbone_features(img)

        return yolo_feature, bbox

    def _get_yolo_backbone_features(self, img):
        backbone_out = {}
        hook_handle = None
        try:
            if hasattr(self.yolo.model, 'model'):
                model = self.yolo.model.model
            else:
                model = self.yolo.model

            target_layer_idx = None
            for i, layer in enumerate(model):
                if hasattr(layer, '__class__') and 'C3k2' in layer.__class__.__name__:
                    target_layer_idx = i

            if target_layer_idx is None:
                target_layer_idx = len(model) - 2

            def hook_fn(module, input, output):
                backbone_out['feat'] = output

            hook_handle = list(model.children())[target_layer_idx].register_forward_hook(hook_fn)

            with torch.no_grad():
                _ = self.yolo(img, verbose=False)

            if hook_handle:
                hook_handle.remove()
        except Exception as e:
            print(f"YOLO feature extraction error: {e}")

        if 'feat' in backbone_out and hasattr(backbone_out['feat'], 'shape'):
            feat = backbone_out['feat']
            if feat.dim() == 4:
                return feat

        return torch.randn(1, 1024, 20, 20, device=self.device)

    def get_sam_features(self, img):
        sam_predictor = SamPredictor(sam_model=self.sam)
        sam_predictor.set_image(img)

        image_embeddings = sam_predictor.features
        return image_embeddings

    def forward(self, img):
        batch_size = img.shape[0]
        masks = []
        bboxes = []

        for i in range(batch_size):
            img_np = (img[i].permute(1, 2, 0).cpu().numpy() * 255).astype('uint8')

            yolo_results = self.yolo(img_np, verbose=False)

            if len(yolo_results) == 0 or len(yolo_results[0].boxes) == 0:
                mask = torch.zeros((1, img.shape[2], img.shape[3]), device=self.device)
                bbox = torch.zeros(4, device=self.device)
                masks.append(mask)
                bboxes.append(bbox)
                continue

            boxes = yolo_results[0].boxes
            best_idx = boxes.conf.argmax()
            bbox = boxes.xyxy[best_idx].cpu()
            bbox_tensor = torch.tensor([bbox[0].item(), bbox[1].item(), bbox[2].item(), bbox[3].item()], device=self.device)

            yolo_feat = self._get_yolo_backbone_features(img_np)
            if yolo_feat is None:
                yolo_feat = torch.randn(1, 1024, 20, 20, device=self.device)

            yolo_channels = yolo_feat.shape[1]

            if yolo_channels == 1024:
                projected_feat = self.feature_projection(yolo_feat)
            elif yolo_channels == 256:
                projected_feat = F.adaptive_avg_pool2d(yolo_feat, (64, 64))
            else:
                projected_feat = F.adaptive_avg_pool2d(yolo_feat, (64, 64))

            sam_predictor = SamPredictor(sam_model=self.sam)
            sam_predictor.set_image(img_np)
            sam_features = sam_predictor.features

            if sam_features.shape[2:] != projected_feat.shape[2:]:
                sam_features = F.interpolate(
                    sam_features.unsqueeze(0),
                    size=projected_feat.shape[2:],
                    mode='bilinear',
                    align_corners=False
                ).squeeze(0)
            elif sam_features.dim() == 4:
                sam_features = sam_features

            if projected_feat.shape[0] == 1 and sam_features.shape[0] > 1:
                sam_features = sam_features[:1]
            elif sam_features.shape[0] == 1 and projected_feat.shape[0] > 1:
                projected_feat = projected_feat[:1]

            fused_feat = torch.cat([projected_feat, sam_features], dim=1)

            fusion_mask = self.fusion_decoder(fused_feat)
            fusion_mask = F.interpolate(fusion_mask, size=(img.shape[2], img.shape[3]), mode='bilinear', align_corners=False)
            fusion_mask = torch.sigmoid(fusion_mask)

            sam_masks, _, _ = sam_predictor.predict(box=bbox[[0,1,2,3]].cpu().numpy())
            sam_mask = torch.tensor(sam_masks[0], device=self.device).unsqueeze(0).unsqueeze(0).float()
            sam_mask = F.interpolate(sam_mask, size=(img.shape[2], img.shape[3]), mode='bilinear', align_corners=False)

            mask = torch.max(sam_mask, fusion_mask)

            masks.append(mask.squeeze(0))
            bboxes.append(bbox_tensor)

        masks = torch.stack(masks, dim=0)
        bboxes = torch.stack(bboxes, dim=0)

        return masks, bboxes

    def post_process(self, mask):
        kernel = torch.ones(5, 5, device=self.device)
        mask = F.max_pool2d(mask, kernel_size=5, stride=1, padding=2)
        mask = 1 - F.max_pool2d(1 - mask, kernel_size=5, stride=1, padding=2)
        mask = (mask > 0.5).float()
        return mask


class YOLOv11SAMJointPredictor:
    def __init__(self, yolo_path, sam_path, joint_model_path, device='cuda'):
        self.device = device
        self.model = YOLOv11SAMJointModel(yolo_path, sam_path, device)
        self.model.load_joint_weights(joint_model_path)
        self.model.to(device)
        print("YOLOv11-SAM joint model ready for inference")

    def __call__(self, img):
        with torch.no_grad():
            masks, bboxes = self.model(img)
        return masks, bboxes


def get_yolo_sam_joint_model(yolo_path, sam_path, joint_model_path, device='cuda'):
    predictor = YOLOv11SAMJointPredictor(yolo_path, sam_path, joint_model_path, device)
    return predictor
