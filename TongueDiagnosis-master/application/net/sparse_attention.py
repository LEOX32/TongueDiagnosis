import torch
import torch.nn as nn

class SparseAttention(nn.Module):
    def __init__(self, dim, num_heads=8, qkv_bias=False, qk_scale=None, dropout_rate=0.0):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** -0.5
        
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(dropout_rate)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(dropout_rate)
        
    def calculate_information_density(self, x):
        """计算特征图的信息密度"""
        # 计算特征的标准差（衡量信息密度）
        std = torch.std(x, dim=-1, keepdim=True)
        
        # 计算特征的梯度（衡量边缘信息）
        # 修复：确保梯度计算的维度正确
        B, N, C = x.shape
        if N > 1:
            # 计算相邻位置的差值
            diff = torch.abs(x[:, 1:] - x[:, :-1])
            grad = torch.mean(diff, dim=-1, keepdim=True)
            # 填充第一个位置
            grad = torch.cat([torch.zeros_like(grad[:, :1]), grad], dim=1)
        else:
            grad = torch.zeros_like(std)
        
        # 综合信息密度
        density = (std + grad) / 2
        return density
    
    def forward(self, x):
        B, N, C = x.shape
        
        # 计算QKV
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # 计算信息密度
        density = self.calculate_information_density(x)
        density = density.squeeze(-1)  # (B, N)
        
        # 生成注意力掩码
        # 只对信息密度高的区域计算完整注意力
        threshold = torch.mean(density) + 0.5 * torch.std(density)
        attention_mask = density > threshold  # (B, N)
        
        # 应用掩码到注意力计算
        attn = (q @ k.transpose(-2, -1)) * self.scale
        
        # 对低信息密度区域应用局部注意力掩码
        local_mask = self.generate_local_mask(N, attention_mask, B)
        attn = attn + local_mask
        
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)
        
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        
        return x
    
    def generate_local_mask(self, N, attention_mask, B):
        """生成局部注意力掩码"""
        # 创建距离矩阵
        positions = torch.arange(N, device=attention_mask.device)
        distance = torch.abs(positions.unsqueeze(0) - positions.unsqueeze(1))
        
        # 只在局部窗口内计算注意力
        local_window = 16
        local_mask = torch.where(distance < local_window, 0, -1e10)
        local_mask = local_mask.unsqueeze(0).unsqueeze(0).repeat(B, self.num_heads, 1, 1)
        
        # 对高信息密度区域禁用局部掩码
        high_info_mask = attention_mask.unsqueeze(1).unsqueeze(1).repeat(1, self.num_heads, N, 1)
        local_mask = torch.where(high_info_mask, 0, local_mask)
        
        return local_mask
