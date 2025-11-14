import motor.motor_asyncio
from beanie import init_beanie
from .config import settings
from .models import User, AnalysisResult # Make sure User is here

async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
    db = client.get_database() 
    await init_beanie(database=db, document_models=[User, AnalysisResult])
    print("Database connection initialized...")