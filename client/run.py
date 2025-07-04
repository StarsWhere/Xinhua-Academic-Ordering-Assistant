# -*- coding: utf-8 -*-
import tkinter as tk
from src.main_app import ISBNApp
import logging

# --- 配置日志记录 ---
# 将日志配置放在主入口，确保在任何模块导入前生效
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    # 捕获Tcl/Tk的内部错误，并记录到日志中
    def report_callback_exception(exc, val, tb):
        import traceback
        error_message = "".join(traceback.format_exception(exc, val, tb))
        logging.error(f"捕获到未处理的Tkinter异常:\n{error_message}")

    root = tk.Tk()
    root.report_callback_exception = report_callback_exception
    
    app = ISBNApp(root)
    root.mainloop()