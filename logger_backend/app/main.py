# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, HTTPException
from pymongo import MongoClient
from .models import LogEntry
import os
import logging

# --- 日志配置 ---
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# --- 连接MongoDB ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
client = MongoClient(MONGO_URI)
db = client.xinhua_platform_logs
log_collection = db.logs

app = FastAPI(
    title="新华平台数据收集服务",
    description="一个用于接收、验证并存储客户端日志的严谨API服务。"
)

@app.on_event("startup")
def startup_db_client():
    try:
        client.admin.command('ping')
        log.info("成功连接到MongoDB。")
    except Exception as e:
        log.error(f"无法连接到MongoDB: {e}")
        raise e

@app.on_event("shutdown")
def shutdown_db_client():
    client.close()
    log.info("MongoDB连接已关闭。")

@app.post("/log", status_code=201, response_model=dict)
async def create_log_entry(log_data: LogEntry, request: Request):
    """
    接收并存储一条新的日志记录。
    - 验证传入数据是否符合 LogEntry 模型。
    - 自动添加客户端IP和createdAt时间戳。
    - 以驼峰命名法（camelCase）将数据存入MongoDB。
    """
    try:
        log_data.client_ip = request.client.host
        
        # [修改] Pydantic V2 推荐使用 model_dump() 方法替代旧的 dict() 方法
        log_dict = log_data.model_dump(by_alias=True, exclude_none=True)
        
        result = log_collection.insert_one(log_dict)
        log.info(f"成功接收并存储日志，文档ID: {result.inserted_id}")
        
        return {"message": "Log received successfully", "id": str(result.inserted_id)}
        
    except Exception as e:
        log.error(f"处理日志条目时发生错误: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing log entry.")

@app.get("/", response_model=dict)
def read_root():
    """根路径，用于健康检查。"""
    return {"message": "欢迎使用新华平台数据收集API - v2.1 (Pydantic V2 兼容版)"}