import uvicorn
from fastapi import FastAPI
from app.controller import router as api_router
import firebase_listener  # start listener

app = FastAPI(title="ESP32 IoT Service")
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
