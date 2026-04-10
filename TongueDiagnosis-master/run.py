import uvicorn
from application.config import settings
from application.models.database import Base, engine
from application.models.models import User, TongueAnalysis, ChatSession, ChatRecord

print("Creating database tables...")
print(f"Models in Base.metadata: {list(Base.metadata.tables.keys())}")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully")

from application import create_app
app = create_app()

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)
