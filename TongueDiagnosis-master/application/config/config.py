import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    SECRET_KEY: str = os.getenv("SECRET_KEY", "f2e1f1b1c1a1")
    ALGORITHMS: str = "HS256"
    IMG_PATH: str = "frontend/public/tongue"
    IMG_DB_PATH: str = "tongue"
    OLLAMA_PATH: str = "http://localhost:11434/api/chat"
    SYSTEM_PROMPT: str = "You are now an AI traditional Chinese medicine doctor specializing in tongue diagnosis. At the very beginning, I will show you four image features of the user's tongue. Please use your knowledge of traditional Chinese medicine to give the user some suggestions."
    LLM_NAME: str = "qwen2.5:3b"
    APP_PORT: int = 5000
    SUPPORTED_LANGUAGES: dict = {
        "en": "English",
        "zh": "中文",
        "es": "Español",
        "fr": "Français",
        "de": "Deutsch",
        "ja": "日本語",
        "ko": "한국어"
    }
    DEFAULT_LANGUAGE: str = "en"

settings = Settings()
