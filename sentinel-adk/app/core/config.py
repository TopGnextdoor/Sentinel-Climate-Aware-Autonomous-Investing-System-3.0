import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROJECT_NAME = "Sentinel API"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

settings = Config()
