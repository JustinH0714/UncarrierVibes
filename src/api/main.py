from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import sentiment, feedback, metrics
from src.api.websocket import manager

app = FastAPI(title="UncarrierVibes API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sentiment.router, prefix="/api/v1/sentiment", tags=["sentiment"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except Exception:
        await manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "Welcome to UncarrierVibes API"}