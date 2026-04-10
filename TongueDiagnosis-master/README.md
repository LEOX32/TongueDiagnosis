# AI 舌诊诊断系统

基于深度学习的中医舌诊智能分析系统，结合 YOLO、SAM 和 ResNet 等先进模型，实现舌象的自动识别与中医诊断建议生成。

## 项目概述

本项目是一个完整的 AI 舌诊应用系统，包含后端 API 服务和前端 Web 界面，支持多语言（中文、英文、西班牙文、法文、德文、日文、韩文），可实现：

- **舌象检测与分割**：使用 YOLO v11 和 Segment Anything Model (SAM) 精确定位并分割舌象区域
- **四诊特征分类**：
  - 舌色分类（5 类）：淡白舌、淡红舌、红舌、绛舌、青紫舌
  - 舌苔颜色（2 类）：白苔、灰黑苔
  - 舌苔厚度（2 类）：薄、厚
  - 腻腐程度（2 类）：腻苔、腐苔
- **健康追踪**：记录和分析用户舌象变化趋势
- **智能问诊**：基于大语言模型（Ollama）提供中医诊断建议

## 技术栈

### 后端技术

- **框架**：FastAPI
- **深度学习**：PyTorch, Ultralytics YOLO, Segment Anything (SAM)
- **数据库**：SQLite + SQLAlchemy
- **认证**：JWT (JSON Web Token)
- **LLM 集成**：Ollama (Qwen2.5:3b)

### 前端技术

- **框架**：Vue 3 + Vite
- **UI 组件库**：Element Plus
- **状态管理**：Pinia + Vuex
- **路由**：Vue Router
- **国际化**：Vue I18n
- **HTTP 客户端**：Axios
- **桌面应用**：Electron

## 项目结构

```
TongueDiagnosis/
├── application/                  # 后端应用核心代码
│   ├── config/                   # 配置文件
│   │   └── config.py
│   ├── core/                     # 核心功能
│   │   └── authentication.py     # JWT 认证
│   ├── models/                   # 数据模型
│   │   ├── models.py             # SQLAlchemy 模型
│   │   ├── schemas.py            # Pydantic 数据验证
│   │   ├── database.py           # 数据库配置
│   │   └── create_*.sql          # SQL 建表语句
│   ├── net/                      # 神经网络模型
│   │   ├── model/                # 模型定义
│   │   │   ├── resnet.py         # 原始 ResNet 模型
│   │   │   ├── resnet_improved.py # 改进 ResNet 模型
│   │   │   └── yolo_sam_joint.py # YOLO-SAM 联合模型
│   │   ├── predict.py            # 预测推理核心
│   │   ├── sparse_sam.py         # 稀疏注意力 SAM
│   │   └── sparse_attention.py   # 稀疏注意力机制
│   ├── orm/
│   │   └── crud/                 # 数据库操作
│   │       ├── auth_user.py
│   │       ├── chat_record.py
│   │       └── tongue_analysis.py
│   ├── routes/                   # API 路由
│   │   ├── model_api.py          # 舌诊模型 API
│   │   ├── user_api.py           # 用户认证 API
│   │   ├── health_track.py       # 健康追踪 API
│   │   └── ollama_used.py        # LLM 对话 API
│   └── __init__.py
├── frontend/                     # 前端 Vue 项目
│   ├── public/
│   │   └── fontawesome-free-7.1.0-web/
│   ├── src/
│   │   ├── assets/               # 静态资源
│   │   ├── components/           # Vue 组件
│   │   ├── config/               # 前端配置
│   │   ├── i18n/                 # 国际化文件
│   │   ├── router/               # 路由配置
│   │   ├── stores/               # 状态管理
│   │   └── views/                # 页面视图
│   ├── index.html
│   ├── main.js
│   ├── package.json
│   └── vite.config.js
├── dataset/                      # 数据集
│   ├── train_labels.csv          # 训练集标签
│   ├── test_labels.csv           # 测试集标签
│   └── val/                      # 验证集图片
├── checkpoints/                  # 预训练模型权重
│   ├── best_model.pth
│   ├── improved_resnet/          # 改进 ResNet 模型
│   │   ├── full_model/
│   │   ├── tongue_color/
│   │   ├── coating_color/
│   │   ├── coating_thickness/
│   │   └── greasy_degree/
│   └── original_resnet/          # 原始 ResNet 模型
├── .env                          # 环境配置
├── .gitignore
├── requirements.txt              # Python 依赖
├── run.py                        # 后端启动脚本
└── train_improved_resnet_full.py # 模型训练脚本
```

## 安装指南

### 环境要求

- Python 3.9+
- Node.js 16+
- NVIDIA GPU（推荐，用于加速推理）
- CUDA 11.8+（如使用 GPU）

### 后端安装

1. **创建虚拟环境**（推荐）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

1. **安装 Python 依赖**

```bash
pip install -r requirements.txt
```

1. **下载模型权重**
   将以下模型文件放到 `application/net/weights/` 目录：

- `yolov11.pt` - YOLO v11 模型
- `sam_vit_b_01ec64.pth` - SAM 模型
- `tongue_color.pth` - 舌色分类模型
- `tongue_coat_color.pth` - 舌苔颜色模型
- `thickness.pth` - 厚度分类模型
- `rot_and_greasy.pth` - 腻腐程度模型

1. **配置环境变量**
   编辑 `.env` 文件：

```bash
# 模型配置
USE_IMPROVED_RESNET=false  # 使用改进 ResNet 模型（推荐设为 true）
IMPROVED_RESNET_PATH=checkpoints/improved_resnet/full_model/best_model.pth

# 数据库配置（可选）
SECRET_KEY=your_secret_key_here

# LLM 配置
OLLAMA_PATH=http://localhost:11434/api/chat
LLM_NAME=qwen2.5:3b
```

1. **安装 Ollama**（可选，用于智能问诊）

```bash
# Windows/Mac
# 从 https://ollama.ai 下载安装

# 拉取模型
ollama pull qwen2.5:3b
```

### 前端安装

1. **进入前端目录**

```bash
cd frontend
```

1. **安装 Node.js 依赖**

```bash
npm install
```

1. **配置前端 API 地址**
   编辑 `frontend/src/config/config.js`，设置后端 API 地址。

## 运行方式

### 启动后端服务

```bash
python run.py
```

服务将在 `http://localhost:5000` 启动。

首次运行时会自动创建数据库表。

### 启动前端开发服务器

```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 启动。

### 构建前端生产版本

```bash
cd frontend
npm run build
```

### 打包 Electron 桌面应用

```bash
cd frontend
npm run electron:build
```

构建产物将在 `dist_electron/` 目录。

## 训练自己的模型

### 准备数据集

数据集应包含：

- 舌象图片（JPG 格式）
- 标签 CSV 文件，包含以下列：
  - `SID`: 图片 ID（与文件名对应）
  - `舌色`: 淡白舌/淡红舌/红舌/绛舌/青紫舌
  - `舌苔颜色`: 白苔/灰黑苔
  - `舌苔厚度`: 薄/厚
  - `腻腐程度`: 腻苔/腐苔

### 训练改进的 ResNet 模型

```bash
python train_improved_resnet_full.py
```

训练脚本会自动：

- 加载数据集
- 使用改进的 ResNet50 架构（注意力门控 + 多尺度卷积）
- 同时训练四个分类任务
- 保存最佳模型到 `checkpoints/improved_resnet/full_model/`

### 自定义训练参数

编辑 `train_improved_resnet_full.py`：

```python
# 修改这些参数
batch_size = 32
epochs = 50
learning_rate = 0.001
img_size = 224
```

## API 接口文档

### 用户认证

#### 注册

```http
POST /api/user/register
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

#### 登录

```http
POST /api/user/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

响应：

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {...}
}
```

### 舌诊分析

#### 上传舌象并分析

```http
POST /api/model/predict
Content-Type: multipart/form-data
Authorization: Bearer <token>

FormData:
- file: [舌象图片]
- record_id: [记录 ID]
```

响应：

```json
{
  "code": 0,
  "tongue_color": "红舌",
  "tongue_coat_color": "白苔",
  "thickness": "薄",
  "rot_and_greasy": "腻苔"
}
```

### 健康追踪

#### 获取历史记录

```http
GET /api/health/history
Authorization: Bearer <token>
```

#### 获取分析建议

```http
GET /api/health/analysis
Authorization: Bearer <token>
```

### LLM 智能问诊

#### 发送消息

```http
POST /api/ollama/chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "我的舌头是什么情况？",
  "context": {...}
}
```

## 核心功能说明

### 1. 舌象检测与分割

系统使用两级检测流程：

1. **YOLO v11**：检测舌象位置，返回边界框
2. **SAM (Segment Anything Model)**：根据边界框生成精确的舌象分割掩码

这种组合确保了即使在复杂背景下也能准确提取舌象区域。

### 2. 四诊特征分类

使用改进的 ResNet50 模型进行多任务学习：

**改进点**：

- **注意力门控机制**：自动关注舌象的重要区域
- **多尺度卷积**：捕捉不同尺度的特征
- **共享 backbone**：四个任务共享特征提取器，提高效率

**分类任务**：

- 舌色（5 类）：反映气血盛衰
- 舌苔颜色（2 类）：判断病邪性质
- 舌苔厚度（2 类）：评估病邪深浅
- 腻腐程度（2 类）：判断湿浊程度

### 3. 健康追踪

系统记录用户的舌诊历史，提供：

- 趋势分析图表
- 体质变化追踪
- 个性化健康建议

### 4. 智能问诊

集成 Ollama LLM，基于舌诊结果提供：

- 中医辨证分析
- 养生建议
- 饮食调理方案

## 模型性能

### 改进 ResNet 模型（50 epochs 训练）

| 任务        | 准确率        |
| --------- | ---------- |
| 舌色分类      | 72.34%     |
| 舌苔颜色      | 98.99%     |
| 舌苔厚度      | 68.45%     |
| 腻腐程度      | 91.23%     |
| **平均准确率** | **82.75%** |

### 消融实验结果

| 模型配置                   | 平均准确率      |
| ---------------------- | ---------- |
| Baseline (标准 ResNet50) | 82.75%     |
| + 注意力门控                | 82.11%     |
| + 多尺度卷积                | **83.20%** |
| Full (注意力 + 多尺度)       | 81.61%     |

**结论**：多尺度卷积模块对性能提升最为显著。

## 数据集说明

### 数据集规模

- 训练集：约 2,700 张图片
- 验证集：约 894 张图片
- 总计：3,594 张舌象图片

### 数据分布

**舌色分布**：

- 淡白舌：\~15%
- 淡红舌：\~35%
- 红舌：\~30%
- 绛舌：\~10%
- 青紫舌：\~10%

**舌苔颜色**：

- 白苔：\~85%
- 灰黑苔：\~15%

## 常见问题

### Q: 模型推理速度慢怎么办？

A:

1. 确保使用 GPU 运行（检查 `torch.cuda.is_available()`）
2. 使用改进的 ResNet 模型（单模型 vs 四个独立模型）
3. 启用模型预热（系统已自动实现）

### Q: 如何切换到改进的 ResNet 模型？

A: 编辑 `.env` 文件，设置 `USE_IMPROVED_RESNET=true`

### Q: Ollama LLM 无法连接？

A:

1. 确保 Ollama 服务已启动：`ollama serve`
2. 检查模型已下载：`ollama pull qwen2.5:3b`
3. 验证 API 地址配置正确

### Q: 前端无法连接后端？

A:

1. 检查后端是否在 5000 端口运行
2. 确认前端配置文件中的 API 地址正确
3. 检查 CORS 设置

### Q: 数据库表创建失败？

A:

1. 删除现有的数据库文件（通常在 `application/orm/` 目录）
2. 重新运行 `python run.py`
3. 检查是否有写入权限

## 许可证

本项目采用 **LGPL-3.0-or-later** 许可证。

## 致谢

- **YOLO v11**: Ultralytics
- **SAM**: Meta AI Research
- **ResNet**: Microsoft Research
- **FastAPI**: Sebastián Ramírez
- **Vue.js**: Evan You
- **Element Plus**: Element Plus Team

## 联系方式

- **作者**: pyx
- **项目版本**: 2.1.0
- **最后更新**: 2026-01

***

**注意**: 本系统仅供学习和研究使用，不能替代专业医生的诊断。如有健康问题，请咨询专业医疗机构。
