import tkinter as tk
from src.main_app import ISBNApp
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    def report_callback_exception(exc, val, tb):
        import traceback
        error_message = "".join(traceback.format_exception(exc, val, tb))
        logging.error(f"捕获到未处理的Tkinter异常:\n{error_message}")

    root = tk.Tk()
    root.report_callback_exception = report_callback_exception
    
    app = ISBNApp(root)
    root.mainloop()