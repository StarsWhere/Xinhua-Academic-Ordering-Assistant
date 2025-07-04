import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import base64
import hashlib
import threading
import logging

def create_login_view(app):
    """创建并显示登录界面。"""
    from .base_view import create_centered_content_frame

    container = create_centered_content_frame(app.root)

    def login_action():
        student_no = student_no_entry.get().strip()
        password = password_entry.get().strip()
        verify_code = verify_code_entry.get().strip()

        if not all([student_no, password, verify_code]):
            messagebox.showwarning("登录失败", "请填写完整的登录信息")
            return

        if save_credentials_var.get():
            app.settings.set("username", student_no)
            app.settings.set_encrypted_password(password)
        else:
            app.settings.set("username", "")
            app.settings.set_encrypted_password("")
        app.settings.set("save_credentials", save_credentials_var.get())
        app.settings.set("allow_data_collection", allow_logging_var.get())
        app.settings.save()

        app.login(student_no, password, verify_code)

    def refresh_captcha():
        def _fetch_task():
            try:
                login_page_url = f"{app.api_client.base_url}/login.do?univ=YJ"
                app.api_client.session.get(login_page_url, timeout=10)

                captcha_url = f"{app.api_client.base_url}/api/getVerifyCode.do"
                headers = app.api_client.get_api_headers("login.do?univ=YJ")
                response = app.api_client.session.get(captcha_url, headers=headers, stream=True, timeout=10)
                
                if response and response.status_code == 200:
                    image_data = response.content
                    image = Image.open(BytesIO(image_data)).resize((120, 40), Image.LANCZOS)
                    app.captcha_photo = ImageTk.PhotoImage(image)
                    captcha_image_label.config(image=app.captcha_photo)
                    threading.Thread(target=_recognize_and_fill_captcha, args=(image_data,), daemon=True).start()
                else:
                    messagebox.showerror("错误", "获取验证码失败。")
            except Exception as e:
                logging.error(f"刷新验证码时出错: {e}")
        
        threading.Thread(target=_fetch_task, daemon=True).start()

    def _recognize_and_fill_captcha(image_data):
        """调用后端OCR服务识别验证码并填充。"""
        b64_image = base64.b64encode(image_data).decode('utf-8')
        logging.info("正在调用后端OCR服务识别验证码...")
        
        ocr_result = app.api_client.call_ocr_service(b64_image)
        
        if ocr_result and ocr_result.get("data") and ocr_result["data"].get("code"):
            recognized_code = ocr_result["data"]["code"]
            verify_code_entry.delete(0, tk.END)
            verify_code_entry.insert(0, recognized_code)
            logging.info(f"验证码自动填充成功: {recognized_code}")
        else:
            logging.warning("验证码自动填充失败，请手动输入。")
    
    ttk.Label(container, text="新华传媒教材征订平台", style='Title.TLabel').pack(pady=(0, 30))
    form_frame = ttk.LabelFrame(container, text="用户登录", padding="20")
    form_frame.pack()

    ttk.Label(form_frame, text="学号:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    student_no_entry = ttk.Entry(form_frame, width=30)
    student_no_entry.grid(row=0, column=1, columnspan=2, pady=5, sticky="we")
    
    ttk.Label(form_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    password_entry = ttk.Entry(form_frame, show="*", width=30)
    password_entry.grid(row=1, column=1, columnspan=2, pady=5, sticky="we")
    
    ttk.Label(form_frame, text="初始密码为: 123456", foreground="gray").grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

    ttk.Label(form_frame, text="验证码:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    verify_code_entry = ttk.Entry(form_frame, width=15)
    verify_code_entry.grid(row=3, column=1, pady=5, sticky="w")
    
    captcha_image_label = ttk.Label(form_frame, text="...", relief="sunken", cursor="hand2")
    captcha_image_label.grid(row=3, column=2, padx=(5,0), pady=5, sticky="w")
    captcha_image_label.bind("<Button-1>", lambda e: refresh_captcha())
    
    options_frame = ttk.Frame(form_frame)
    options_frame.grid(row=4, column=0, columnspan=3, pady=5, sticky="w")
    
    save_credentials_var = tk.BooleanVar(value=app.settings.get("save_credentials"))
    ttk.Checkbutton(options_frame, text="保存密码", variable=save_credentials_var).pack(side=tk.LEFT)
    
    allow_logging_var = tk.BooleanVar(value=app.settings.get("allow_data_collection"))
    ttk.Checkbutton(options_frame, text="协助优化", variable=allow_logging_var).pack(side=tk.LEFT, padx=(20, 0))

    if save_credentials_var.get():
        student_no_entry.insert(0, app.settings.get("username"))
        password_entry.insert(0, app.settings.get_decrypted_password())

    button_frame = ttk.Frame(form_frame)
    button_frame.grid(row=5, column=0, columnspan=3, pady=10)
    
    ttk.Button(button_frame, text="登录", command=login_action, style="Accent.TButton").pack(side=tk.LEFT, padx=10, ipadx=10)
    ttk.Button(button_frame, text="刷新验证码", command=refresh_captcha).pack(side=tk.LEFT, padx=10)
    
    fg_label = ttk.Label(form_frame, text="忘记密码?", foreground="blue", cursor="hand2")
    fg_label.grid(row=6, column=0, columnspan=3, pady=(5, 0))
    fg_label.bind("<Button-1>", lambda e: app.show_forget_password_page())

    ttk.Label(form_frame, text="上海应用技术大学专用", foreground="darkgray").grid(row=7, column=0, columnspan=3, pady=(10, 0))
    ttk.Label(form_frame, text="奉贤和徐汇校区通用", foreground="darkgray").grid(row=8, column=0, columnspan=3, pady=(0, 5))

    app.root.bind('<Return>', lambda e: login_action())
    refresh_captcha()