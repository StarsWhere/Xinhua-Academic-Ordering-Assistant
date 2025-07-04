# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, HTTPException
from pymongo import MongoClient
from .models import LogEntry
import os
import logging
import json # 新增导入
import requests # 新增导入，用于OCR转发

# --- 日志配置 ---
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# --- 连接MongoDB ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
client = MongoClient(MONGO_URI)
db = client.xinhua_platform_logs
log_collection = db.logs

# --- OCR配置 ---
# 从环境变量读取OCR服务地址，如果未设置，则默认使用原前端地址
OCR_API_URL = os.getenv("OCR_API_URL", "https://ocr.xiaoying.life/v1/school-captcha")
if not OCR_API_URL:
    log.warning("OCR_API_URL 环境变量未设置，OCR功能可能无法正常工作。")

# --- 版本信息文件路径 ---
# 假设 version_info.json 和 main.py 在同一个父目录 (app 文件夹的父目录)
# 在docker-compose中，api服务的工作目录是 /code，而 version_info.json 应该在 /code
# 所以从 /code/app 下的 main.py 访问，路径是 ../version_info.json
VERSION_INFO_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "version_info.json")

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

@app.post("/ocr_captcha")
async def ocr_captcha_endpoint(request: Request):
    """
    代理验证码OCR识别请求到第三方服务。
    """
    if not OCR_API_URL:
        log.error("OCR API URL 未配置，无法提供OCR服务。")
        raise HTTPException(status_code=503, detail="OCR service not configured.")
    
    try:
        request_body = await request.json()
        log.info(f"转发OCR请求到: {OCR_API_URL}")
        
        # 转发请求到OCR服务
        ocr_response = requests.post(OCR_API_URL, json=request_body, timeout=10)
        ocr_response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        
        return ocr_response.json()
    except requests.exceptions.RequestException as e:
        log.error(f"OCR服务请求失败: {e}")
        raise HTTPException(status_code=502, detail=f"OCR service communication error: {e}")
    except json.JSONDecodeError:
        log.error("接收到的OCR请求体不是有效的JSON。")
        raise HTTPException(status_code=400, detail="Invalid JSON request body.")
    except Exception as e:
        log.error(f"处理OCR请求时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during OCR processing.")

@app.get("/version_check")
async def version_check_endpoint(client_version: str):
    """
    检查客户端版本并推送更新信息。
    """
    try:
        with open(VERSION_INFO_FILE, 'r', encoding='utf-8') as f:
            version_info = json.load(f)
        
        latest_version_number = version_info.get("latestVersionNumber", "0.0.0")
        latest_version_url = version_info.get("latestVersionUrl", "")
        release_note = version_info.get("releaseNote", "")

        # 简单的版本比较，可以根据实际需求使用更复杂的版本号解析库
        should_update = False
        try:
            # 将版本号拆分为数字进行比较
            client_parts = [int(x) for x in client_version.split('.')]
            latest_parts = [int(x) for x in latest_version_number.split('.')]

            # 填充较短的版本号，使其长度一致，方便比较 (例如 1.0 vs 1.0.0)
            max_len = max(len(client_parts), len(latest_parts))
            client_parts += [0] * (max_len - len(client_parts))
            latest_parts += [0] * (max_len - len(latest_parts))
            
            if latest_parts > client_parts:
                should_update = True
        except ValueError:
            log.warning(f"无法解析版本号：客户端'{client_version}', 最新'{latest_version_number}'")
            # 如果版本号解析失败，保守起见不强制更新，或者可以根据业务需求决定
            should_update = False # 或者设置为True以强制用户更新到一个可解析的版本

        response = {
            "shouldUpdate": should_update
        }
        if should_update:
            response["latestVersionUrl"] = latest_version_url
            response["releaseNote"] = release_note
        
        log.info(f"客户端版本: {client_version}, 最新版本: {latest_version_number}, 是否更新: {should_update}")
        return response

    except FileNotFoundError:
        log.error(f"版本信息文件未找到: {VERSION_INFO_FILE}")
        raise HTTPException(status_code=404, detail="Version information not found.")
    except json.JSONDecodeError:
        log.error(f"版本信息文件格式错误: {VERSION_INFO_FILE}")
        raise HTTPException(status_code=500, detail="Version information file is malformed.")
    except Exception as e:
        log.error(f"处理版本检查请求时发生错误: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during version check.")

@app.get("/", response_model=dict)
def read_root():
    """根路径，用于健康检查。"""
    return {"message": "欢迎使用新华平台数据收集API - v2.1 (Pydantic V2 兼容版)"}