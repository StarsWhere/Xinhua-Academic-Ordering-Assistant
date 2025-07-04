# 新华传媒教材征订助手

这是一个为新华传媒教材征订平台开发的第三方桌面客户端应用及其配套的日志收集后端服务。本应用旨在提供一个便捷的图形界面，帮助用户更高效地完成教材征订相关操作。

## 项目结构

本项目包含两个主要部分：

1.  **`client/`**: 基于 Python 和 Tkinter 开发的桌面客户端应用。
2.  **`logger_backend/`**: 基于 FastAPI 和 MongoDB 开发的日志收集后端服务。

## 客户端 (`client/`)

### 描述

**新华传媒教材征订助手** 客户端是一个用户友好的 GUI 界面，允许学生登录、浏览教材、下订单、查看订单历史、重置密码以及绑定手机号。作为第三方工具，它通过模拟官方网站的 API 请求与新华传媒的后端服务进行交互，所有业务逻辑均在本地客户端处理。

### 主要特性

*   用户登录与自动登录（通过会话文件）
*   教材选择与订购
*   订单历史与详情查看
*   密码找回与重置
*   手机号绑定
*   支付确认流程（支付宝/微信，显示免责声明）
*   日志记录（输出到 `app.log` 文件和控制台）

### 运行方式

1.  **安装依赖**:
    ```bash
    # 进入客户端目录
    cd client
    # 建议在虚拟环境中安装
    python -m venv venv
    .\venv\Scripts\activate # Windows
    # source venv/bin/activate # macOS/Linux
    pip install -r requirements.txt
    ```
    (请注意：`requirements.txt` 文件在当前提供的文件列表中未直接显示，您可能需要手动创建或补充此文件，包含 `tkinter`, `requests`, `Pillow` 等依赖。)

2.  **运行应用**:
    ```bash
    python run.py
    ```

## 日志后端 (`logger_backend/`)

### 描述

日志后端服务是一个轻量级的 API，用于接收客户端发送的日志数据，并将其存储到 MongoDB 数据库中。它使用 FastAPI 框架，并支持 Docker 部署。

### 主要特性

*   基于 FastAPI 构建，提供 RESTful API。
*   接收并验证日志数据。
*   将日志数据存储到 MongoDB。
*   自动添加客户端 IP 和时间戳。
*   支持 Docker 和 Docker Compose 部署。

### 运行方式

日志后端服务推荐使用 Docker Compose 运行，因为它包含了 MongoDB 数据库。

1.  **确保已安装 Docker 和 Docker Compose**。

2.  **进入日志后端目录**:
    ```bash
    cd logger_backend
    ```

3.  **启动服务**:
    ```bash
    docker-compose up --build -d
    ```
    这将构建 Docker 镜像，并启动 `api` 服务（FastAPI 应用）和 `mongodb` 服务。

4.  **验证服务**:
    打开浏览器或使用 `curl` 访问 `http://localhost:6656/`，您应该看到欢迎信息：
    `{"message": "欢迎使用新华平台数据收集API - v2.1 (Pydantic V2 兼容版)"}`

### API 端点

*   **POST `/log`**: 接收并存储日志记录。
    *   请求体: `LogEntry` 模型 (包含 `level`, `message`, `timestamp`, `event_type`, `details` 等字段)。
*   **GET `/`**: 健康检查端点。

## 许可证

本项目使用 MIT 许可证。详见 [`LICENSE`](LICENSE) 文件。

## 致谢

感谢所有为本项目提供支持和贡献的人。