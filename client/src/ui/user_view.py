# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox

def create_forget_password_view(app):
    """创建并显示忘记密码界面。"""
    from .base_view import create_centered_content_frame
    container = create_centered_content_frame(app.root)

    def send_code_action():
        student_code = student_code_entry.get().strip()
        mobile_no = mobile_no_entry.get().strip()
        if not student_code or not mobile_no:
            messagebox.showwarning("输入错误", "学号和手机号码不能为空!")
            return
        app.handle_send_forget_password_code(student_code, mobile_no)

    def reset_password_action():
        student_code = student_code_entry.get().strip()
        mobile_no = mobile_no_entry.get().strip()
        validate_code = validate_code_entry.get().strip()
        if not student_code or not mobile_no or not validate_code:
            messagebox.showwarning("输入错误", "学号、手机号码和短信验证码不能为空!")
            return
        app.handle_reset_password(student_code, mobile_no, validate_code)

    ttk.Label(container, text="重置密码", style='Title.TLabel').pack(pady=(0, 30))
    form_frame = ttk.LabelFrame(container, text="忘记密码", padding="20")
    form_frame.pack()

    ttk.Label(form_frame, text="学号:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    student_code_entry = ttk.Entry(form_frame, width=30)
    student_code_entry.grid(row=0, column=1, columnspan=2, pady=5, sticky="we")

    ttk.Label(form_frame, text="手机号码:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    mobile_no_entry = ttk.Entry(form_frame, width=30)
    mobile_no_entry.grid(row=1, column=1, columnspan=2, pady=5, sticky="we")

    ttk.Label(form_frame, text="短信验证码:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    validate_code_entry = ttk.Entry(form_frame, width=15)
    validate_code_entry.grid(row=2, column=1, pady=5, sticky="w")
    ttk.Button(form_frame, text="发送验证码", command=send_code_action).grid(row=2, column=2, padx=(5,0), pady=5, sticky="w")

    button_frame = ttk.Frame(form_frame)
    button_frame.grid(row=3, column=0, columnspan=3, pady=10)
    ttk.Button(button_frame, text="确认重置", command=reset_password_action, style="Accent.TButton").pack(side=tk.LEFT, padx=10, ipadx=10)
    ttk.Button(button_frame, text="返回登录", command=app.go_back_to_login).pack(side=tk.LEFT, padx=10)


def create_bind_phone_view(app):
    """创建并显示绑定手机界面。"""
    from .base_view import create_centered_content_frame
    container = create_centered_content_frame(app.root)

    def send_code_action():
        mobile_no = mobile_no_entry.get().strip()
        if not mobile_no:
            messagebox.showwarning("输入错误", "手机号码不能为空!")
            return
        app.handle_send_bind_phone_code(mobile_no)

    def bind_phone_action():
        mobile_no = mobile_no_entry.get().strip()
        validate_code = validate_code_entry.get().strip()
        if not mobile_no or not validate_code:
            messagebox.showwarning("输入错误", "手机号码和短信验证码不能为空!")
            return
        app.handle_bind_phone(mobile_no, validate_code)

    ttk.Label(container, text="绑定手机号", style='Title.TLabel').pack(pady=(0, 30))
    form_frame = ttk.LabelFrame(container, text="为了您的账户安全，请绑定手机", padding="20")
    form_frame.pack()

    ttk.Label(form_frame, text="手机号码:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    mobile_no_entry = ttk.Entry(form_frame, width=30)
    mobile_no_entry.grid(row=0, column=1, columnspan=2, pady=5, sticky="we")

    ttk.Label(form_frame, text="短信验证码:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    validate_code_entry = ttk.Entry(form_frame, width=15)
    validate_code_entry.grid(row=1, column=1, pady=5, sticky="w")
    ttk.Button(form_frame, text="发送验证码", command=send_code_action).grid(row=1, column=2, padx=(5,0), pady=5, sticky="w")

    button_frame = ttk.Frame(form_frame)
    button_frame.grid(row=2, column=0, columnspan=3, pady=10)
    ttk.Button(button_frame, text="确认绑定", command=bind_phone_action, style="Accent.TButton").pack(side=tk.LEFT, padx=10, ipadx=10)
    ttk.Button(button_frame, text="重新登录", command=app.logout).pack(side=tk.LEFT, padx=10)