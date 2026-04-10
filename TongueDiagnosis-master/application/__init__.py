from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import register_routes
from .models import models
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

def create_app():
    app = FastAPI()
    origins = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
        "*"  # 允许所有来源（生产环境）
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动时预加载模型"""
        print("=" * 50)
        print("应用启动中，正在预加载模型...")
        print("=" * 50)
        from .net.predict import TonguePredictor
        import os
        
        # 检查是否启用改进的 ResNet 模型
        use_improved = True
        improved_model_path = 'checkpoints/improved_resnet/full_model/best_model.pth'

        if use_improved:
            print(f"✅ 使用改进的 ResNet 多输出模型")
            print(f"   模型路径：{improved_model_path}")
            print(f"   特性：注意力门控 + 多尺度卷积 + 4特征联合预测")
        else:
            print(f"ℹ️ 使用原始 ResNet 模型（4 个独立模型）")

        TonguePredictor(
            use_improved_resnet=use_improved,
            improved_resnet_path=improved_model_path,
            use_multi_output=True
        )
        print("=" * 50)
        print("模型预加载完成，应用已就绪！")
        print("=" * 50)
    
    register_routes(app)
    return app
