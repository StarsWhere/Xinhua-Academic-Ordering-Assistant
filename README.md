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

### 如何使用 (开发/调试)

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/StarsWhere/ISBN.git # 假设您的仓库名为ISBN
    cd ISBN
    ```

2.  **设置客户端环境**:
    *   **进入客户端目录**:
        ```bash
        cd client
        ```
    *   **创建并激活虚拟环境** (推荐):
        ```bash
        python -m venv .venv
        # Windows:
        .\venv\Scripts\activate
        # macOS/Linux:
        # source .venv/bin/activate
        ```
    *   **安装依赖**:
        ```bash
        pip install -r requirements.txt
        ```
    *   **运行客户端**:
        ```bash
        python run.py
        ```
        客户端启动后，您将看到登录界面。

3.  **设置日志后端环境**:
    *   **确保已安装 Docker 和 Docker Compose**。
    *   **进入日志后端目录**:
        ```bash
        cd logger_backend
        ```
    *   **启动服务**:
        ```bash
        docker-compose up --build -d
        ```
        这将构建 Docker 镜像，并启动 `api` 服务（FastAPI 应用）和 `mongodb` 服务。
    *   **验证服务**:
        打开浏览器或使用 `curl` 访问 `http://localhost:6656/`，您应该看到欢迎信息：
        `{"message": "欢迎使用新华平台数据收集API - v2.1 (Pydantic V2 兼容版)"}`

### API 端点 (日志后端)

*   **POST `/log`**: 接收并存储日志记录。
    *   请求体: `LogEntry` 模型 (包含 `level`, `message`, `timestamp`, `event_type`, `details` 等字段)。
*   **GET `/`**: 健康检查端点。

### 如何使用 (打包后的客户端)

如果您只想运行客户端应用，可以使用打包好的可执行文件（仅限 Windows）。

1.  **下载最新版本**:
    从项目的 GitHub Releases 页面下载最新版本的 `新华传媒教材征订助手.exe` 文件。

2.  **运行**:
    双击下载的 `新华传媒教材征订助手.exe` 文件即可运行应用程序。无需安装 Python 或其他依赖。

    **注意**: 打包后的客户端默认配置为连接 `https://api.school.starswhere.xyz:44/log` 作为日志后端。如果您希望使用自己的日志后端，需要修改客户端源代码并重新打包。

## 许可证

本项目使用 MIT 许可证。详见 [`LICENSE`](LICENSE) 文件。

## 致谢

感谢所有为本项目提供支持和贡献的人。