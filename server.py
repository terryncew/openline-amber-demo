from fastapi import FastAPI
from amber_api import router as amber_router

app = FastAPI(title="OpenLine Amber Loop")
@app.get("/health") def health(): return {"ok": True}
app.include_router(amber_router, prefix="/api")
