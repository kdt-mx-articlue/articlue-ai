from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.api.routes.pipeline import router as pipeline_router

app = FastAPI(title="AI Pipeline API")

app.include_router(pipeline_router)