from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routers import auth, cats, weights

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

@app.get("/")
def root():
    return {"message": "猫咪成长健康管理系统 API"}

# 导入初始数据
from init_data import init_data
init_data()
