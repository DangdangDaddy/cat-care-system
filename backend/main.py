from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from database import engine
import models
from routers import auth, cats, weights, medical_history, photos, albums

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="猫咪成长健康管理系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cats.router)
app.include_router(weights.router)
app.include_router(medical_history.router)
app.include_router(photos.router)
app.include_router(albums.router)

# 挂载静态文件目录（用于头像等）
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def root():
    return {"message": "猫咪成长健康管理系统 API"}

# 导入初始数据
from init_data import init_data
init_data()
