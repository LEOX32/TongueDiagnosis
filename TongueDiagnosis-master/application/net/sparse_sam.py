import torch
import numpy as np
from segment_anything import sam_model_registry, SamPredictor
from .sparse_attention import SparseAttention

class SparseSamPredictor:
    def __init__(self, sam_model, max_cache_size=10):
        """初始化稀疏注意力SAM预测器"""
        self.sam = sam_model
        self.predictor = SamPredictor(sam_model)
        self.sparse_attention = SparseAttention(dim=768, num_heads=12)
        self.embedding_cache = {}  # 添加缓存机制
        self.cache_keys = []  # 用于跟踪缓存顺序
        self.max_cache_size = max_cache_size  # 最大缓存大小
    
    def set_image(self, image):
        """设置输入图像"""
        self.predictor.set_image(image)
    
    def predict(self, box=None, point_coords=None, point_labels=None, mask_input=None, 
                multimask_output=True, return_logits=False):
        """使用稀疏注意力进行预测"""
        # 获取图像嵌入
        image_embedding = self.predictor.get_image_embedding()
        
        # 生成缓存键
        cache_key = self.generate_cache_key(image_embedding)
        
        # 检查缓存
        if cache_key in self.embedding_cache:
            sparse_embedding = self.embedding_cache[cache_key]
            # 将访问的键移到列表末尾（最近使用）
            if cache_key in self.cache_keys:
                self.cache_keys.remove(cache_key)
            self.cache_keys.append(cache_key)
        else:
            # 应用稀疏注意力
            sparse_embedding = self.apply_sparse_attention(image_embedding)
            
            # 检查缓存大小，如果超过限制，移除最旧的项
            if len(self.embedding_cache) >= self.max_cache_size and self.max_cache_size > 0:
                oldest_key = self.cache_keys.pop(0)
                if oldest_key in self.embedding_cache:
                    del self.embedding_cache[oldest_key]
            
            # 保存到缓存
            self.embedding_cache[cache_key] = sparse_embedding
            self.cache_keys.append(cache_key)
        
        # 直接使用稀疏注意力处理后的嵌入进行预测
        # 不再保存和恢复原始嵌入，减少数据传输
        self.predictor.features = sparse_embedding
        
        # 执行预测
        masks, scores, logits = self.predictor.predict(
            box=box, 
            point_coords=point_coords, 
            point_labels=point_labels, 
            mask_input=mask_input, 
            multimask_output=multimask_output, 
            return_logits=return_logits
        )
        
        return masks, scores, logits
    
    def generate_cache_key(self, embedding):
        """生成嵌入的缓存键"""
        # 使用嵌入的形状和均值作为缓存键
        shape = tuple(embedding.shape)
        mean_val = embedding.mean().item()
        return (shape, round(mean_val, 4))
    
    def apply_sparse_attention(self, image_embedding):
        """对图像嵌入应用稀疏注意力"""
        # 确保稀疏注意力模块在与嵌入相同的设备上
        device = image_embedding.device
        self.sparse_attention.to(device)
        
        # 调整维度 - 使用更高效的内存操作
        B, C, H, W = image_embedding.shape
        # 直接在原设备上执行操作，避免设备间数据传输
        x = image_embedding.flatten(2).transpose(1, 2)  # (B, H*W, C)
        
        # 应用稀疏注意力
        x = self.sparse_attention(x)
        
        # 恢复原始维度
        x = x.transpose(1, 2).reshape(B, C, H, W)
        
        return x
    
    def get_image_embedding(self):
        """获取图像嵌入"""
        return self.predictor.get_image_embedding()

class SparseSamModel:
    def __init__(self, model_type="vit_b", checkpoint=None, device=None):
        """初始化稀疏注意力SAM模型"""
        # 自动选择设备
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 初始化模型并移动到指定设备
        self.sam = sam_model_registry[model_type](checkpoint=checkpoint)
        self.sam.to(device)
        
        # 初始化预测器，设置缓存大小
        self.predictor = SparseSamPredictor(self.sam, max_cache_size=10)
        self.device = device
    
    def get_predictor(self):
        """获取预测器"""
        return self.predictor
    
    def get_device(self):
        """获取当前使用的设备"""
        return self.device
