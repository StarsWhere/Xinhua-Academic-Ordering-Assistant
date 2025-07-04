# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

def to_camel(string: str) -> str:
    """将 snake_case 转换为 camelCase"""
    parts = string.split('_')
    return parts[0] + ''.join(x.title() for x in parts[1:])

class CamelCaseModel(BaseModel):
    """
    一个基础模型，自动将字段名转换为驼峰命名法作为别名。
    此模型已适配 Pydantic V2 版本。
    """
    # model_config 字典作为类属性定义，而不是从外部导入
    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

class RequestInfo(CamelCaseModel):
    method: str
    url: str
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None

class ResponseInfo(CamelCaseModel):
    status_code: int
    headers: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None

class LogEntry(CamelCaseModel):
    """
    定义日志条目的数据结构。
    所有字段在序列化为JSON或字典时都会使用驼峰命名法别名。
    """
    event_type: str
    student_id: Optional[str] = None
    student_no: Optional[str] = None
    timestamp: datetime
    
    request: RequestInfo
    response: Optional[ResponseInfo] = None
    error: Optional[str] = None
    
    client_ip: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")