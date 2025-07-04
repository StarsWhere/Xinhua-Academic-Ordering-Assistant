import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import requests
import os
import json
import hashlib
import logging
import webbrowser

from .settings import AppSettings
from .api_client import ApiClient
from .ui import base_view, login_view, book_view, order_view, user_view

CLIENT_VERSION = "1.1.0" 

class ISBNApp:
    """
    新华传媒教材征订平台GUI应用主调度类。
    负责初始化应用、管理用户会话、调度视图显示及处理核心业务逻辑。
    """
    def __init__(self, root):
        self.root = root
        self.root.title("新华传媒教材征订平台")
        self.root.geometry("1000x750")
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.center_window()
        
        self.settings = AppSettings()
        self.api_client = ApiClient(self.settings)
        self.session_file = "session_data.json"
        
        self.book_widgets = {}
        self.all_books_data = []
        self.current_order_data = None
        
        base_view.setup_styles()
        if self.try_auto_login():
            self._post_login_actions()
        else:
            self.show_login_page()
            self._check_for_updates_on_startup()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _post_login_actions(self):
        """登录后的通用处理，包括检查手机号绑定和版本更新。"""
        if not self.api_client.student_info.get('mobile'):
            messagebox.showinfo("提示", "您的账户尚未绑定手机号，请先绑定。")
            self.show_bind_phone_page()
        else:
            self.show_book_selection_page()
        self._check_for_updates_on_startup()

    def _check_for_updates_on_startup(self):
        """在启动时检查版本更新并显示提示。"""
        def task():
            logging.info(f"当前客户端版本: {CLIENT_VERSION}")
            update_info = self.api_client.check_for_updates(CLIENT_VERSION)
            if update_info and update_info.get("shouldUpdate"):
                release_note = update_info.get("releaseNote", "无详细更新说明。")
                latest_version_url = update_info.get("latestVersionUrl", "")

                dialog = tk.Toplevel(self.root)
                dialog.title("新版本可用")
                dialog.transient(self.root)
                dialog.grab_set()
                dialog.geometry("500x400")
                dialog.resizable(False, False)
                
                dialog.update_idletasks()
                x = (self.root.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
                y = (self.root.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
                dialog.geometry(f"+{x}+{y}")

                main_frame = ttk.Frame(dialog, padding=15)
                main_frame.pack(fill="both", expand=True)
                main_frame.grid_rowconfigure(1, weight=1)
                main_frame.grid_columnconfigure(0, weight=1)

                ttk.Label(main_frame, text="发现新版本！", style="Title.TLabel").grid(row=0, column=0, pady=(0, 10))

                text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("微软雅黑", 10), relief="solid", borderwidth=1, padx=5, pady=5)
                text_widget.insert(tk.END, release_note)
                text_widget.config(state=tk.DISABLED)
                text_widget.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

                scrollbar = ttk.Scrollbar(main_frame, command=text_widget.yview)
                scrollbar.grid(row=1, column=1, sticky="ns")
                text_widget.config(yscrollcommand=scrollbar.set)

                button_frame = ttk.Frame(main_frame)
                button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

                if latest_version_url:
                    ttk.Button(button_frame, text="立即更新", command=lambda: webbrowser.open_new(latest_version_url)).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="稍后更新", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            else:
                logging.info("当前是最新版本或无法获取更新信息。")
        
        import threading
        threading.Thread(target=task, name="VersionCheckThread", daemon=True).start()

    def show_login_page(self):
        base_view.clear_frame(self.root)
        login_view.create_login_view(self)

    def show_book_selection_page(self):
        base_view.clear_frame(self.root)
        book_view.create_book_selection_view(self)
        
    def show_order_history_page(self):
        base_view.clear_frame(self.root)
        order_view.create_order_history_view(self)

    def show_order_detail_page(self, order_id):
        base_view.clear_frame(self.root)
        order_view.create_order_detail_view(self, order_id)
        
    def show_forget_password_page(self):
        base_view.clear_frame(self.root)
        user_view.create_forget_password_view(self)
    
    def show_bind_phone_page(self):
        base_view.clear_frame(self.root)
        user_view.create_bind_phone_view(self)

    def go_back_to_login(self):
        self.show_login_page()

    def try_auto_login(self):
        """尝试自动登录。"""
        if not os.path.exists(self.session_file):
            return False
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.api_client.session.cookies.update(data["cookies"])
            self.api_client.student_info = data["student_info"]
            student_id = self.api_client.student_info.get("studentID")

            if not student_id or not self.validate_session(student_id):
                self.clear_session_data()
                return False

            logging.info("会话有效,自动登录成功。")
            return True
        except Exception as e:
            logging.error(f"加载会话文件时出错: {e}。")
            self.clear_session_data()
            return False

    def validate_session(self, student_id):
        """验证当前会话是否有效。"""
        url = f"{self.api_client.base_url}/api/GetStudentInfo.do"
        param = {"studentID": student_id}
        headers = self.api_client.get_api_headers("myBook.do")
        response = self.api_client.api_request("POST", url, event_type="VALIDATE_SESSION", json=param, headers=headers, timeout=5)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0" and result.get("data"):
                self.api_client.student_info = result["data"][0]
                return True
        return False

    def save_session_data(self):
        """保存会话数据到文件。"""
        data_to_save = {
            "cookies": self.api_client.session.cookies.get_dict(),
            "student_info": self.api_client.student_info
        }
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"保存会话数据失败: {e}")

    def clear_session_data(self):
        """清除本地会话数据。"""
        self.api_client.session = requests.Session()
        self.api_client.student_info = {}
        if os.path.exists(self.session_file):
            os.remove(self.session_file)

    def logout(self):
        """执行用户登出操作。"""
        logging.info("正在登出...")
        self.clear_session_data()
        messagebox.showinfo("登出", "您已成功登出。")
        self.show_login_page()

    def login(self, student_no, password, verify_code):
        """处理用户登录逻辑。"""
        md5_password = hashlib.md5(password.encode('utf-8')).hexdigest()
        login_data = {"univ": "应用技术大学", "studentNo": student_no, "pwd": md5_password, "verifyCode": verify_code}
        headers = self.api_client.get_api_headers("login.do?univ=YJ")
        url = f"{self.api_client.base_url}/api/StudentLogin.do"
        
        response = self.api_client.api_request("POST", url, event_type="LOGIN", json=login_data, headers=headers, timeout=10)
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                student_id = result.get("data")
                if self.get_student_info(student_id):
                    self.save_session_data()
                    self._post_login_actions()
            else:
                messagebox.showerror("登录失败", result.get("errorMsg", "未知错误"))
                self.show_login_page()
        else:
            messagebox.showerror("登录失败", "网络错误或服务器无响应。")
            self.show_login_page()

    def get_student_info(self, student_id):
        """获取学生信息。"""
        url = f"{self.api_client.base_url}/api/GetStudentInfo.do"
        param = {"studentID": student_id}
        headers = self.api_client.get_api_headers("myBook.do")
        response = self.api_client.api_request("POST", url, event_type="GET_STUDENT_INFO", json=param, headers=headers, timeout=10)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0" and result.get("data"):
                self.api_client.student_info = result["data"][0]
                return True
        messagebox.showerror("错误", "无法获取学生信息。")
        return False
        
    def handle_send_forget_password_code(self, student_code, mobile_no):
        """处理发送忘记密码验证码。"""
        response = self.api_client.send_forget_password_code(student_code, mobile_no)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                messagebox.showinfo("发送成功", "验证码已发送，请注意查收。")
            else:
                messagebox.showerror("发送失败", result.get("errorMsg", "未知错误"))
        else:
            messagebox.showerror("网络错误", "发送验证码请求失败。")

    def handle_reset_password(self, student_code, mobile_no, validate_code):
        """处理重置密码。"""
        response = self.api_client.reset_password(student_code, mobile_no, validate_code)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                messagebox.showinfo("成功", "密码重置成功！")
                self.go_back_to_login()
            else:
                messagebox.showerror("重置失败", result.get("errorMsg", "未知错误"))
        else:
            messagebox.showerror("网络错误", "重置密码请求失败。")

    def handle_send_bind_phone_code(self, mobile_no):
        """处理发送绑定手机验证码。"""
        response = self.api_client.send_bind_phone_code(mobile_no)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                messagebox.showinfo("发送成功", "验证码已发送，请注意查收。")
            else:
                messagebox.showerror("发送失败", result.get("errorMsg", "未知错误"))
        else:
            messagebox.showerror("网络错误", "发送验证码请求失败。")

    def handle_bind_phone(self, mobile_no, validate_code):
        """处理绑定手机。"""
        response = self.api_client.bind_phone(mobile_no, validate_code)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                messagebox.showinfo("成功", "手机绑定成功！")
                self.api_client.student_info['mobile'] = mobile_no
                self.save_session_data()
                self.show_book_selection_page()
            else:
                messagebox.showerror("绑定失败", result.get("errorMsg", "未知错误"))
        else:
            messagebox.showerror("网络错误", "绑定手机请求失败。")

    def place_order(self):
        """提交教材订单。"""
        selected_books = [
            {"bookID": info['data'].get("bookID"), "courseNo": info['data'].get("courseNo"),
             "classNo": info['data'].get("classNo"), "course": info['data'].get("course"),
             "teacher": info['data'].get("teacher")}
            for info in self.book_widgets.values() if info['var'].get()
        ]
        
        if not selected_books:
            messagebox.showwarning("提示", "请选择至少一本教材进行订购!")
            return

        order_data = {"studentID": self.api_client.student_info.get('studentID'), "type": "N", "books": selected_books}
        url = f"{self.api_client.base_url}/api/BuildOrder.do"
        headers = self.api_client.get_api_headers("myBook.do")
        
        response = self.api_client.api_request("POST", url, event_type="CREATE_ORDER", json=order_data, headers=headers, timeout=15)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                order_id = result.get("data")
                messagebox.showinfo("成功", f"订单已成功创建!\n订单号: {order_id}")
                self.show_order_detail_page(order_id)
            else:
                messagebox.showerror("订购失败", result.get("errorMsg", "未知错误"))
    
    def get_order_details(self, order_id):
        """获取订单详情。"""
        url = f"{self.api_client.base_url}/api/GetOrder.do"
        headers = self.api_client.get_api_headers(f"order.do?order_id={order_id}")
        param = {"studentID": self.api_client.student_info.get('studentID'), "orderID": order_id}
        
        response = self.api_client.api_request("POST", url, event_type="GET_ORDER_DETAIL", json=param, headers=headers, timeout=10)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0" and result.get("data"):
                return result["data"][0]
        messagebox.showerror("失败", "获取订单详情失败")
        return None

    def get_payment_url(self, payment_type):
        """获取支付链接。"""
        order_id = self.current_order_data.get('orderID')
        amount = self.current_order_data.get('amount', 0)
        
        if payment_type == "alipay":
            url = f"{self.api_client.base_url}/pay/getalipayurl.do?order_id={order_id}&order_amount={amount:.2f}"
            event = "GET_ALIPAY_URL"
        elif payment_type == "wechat":
            url = f"{self.api_client.base_url}/wxPay/getWxPayUrl.do?order_id={order_id}&order_amount={amount:.2f}"
            event = "GET_WXPAY_URL"
        else:
            return None
            
        headers = self.api_client.get_api_headers(f"order.do?order_id={order_id}")
        response = self.api_client.api_request("GET", url, event_type=event, headers=headers, timeout=10)
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get("ok") and result.get("message"):
                return result.get("message")
        messagebox.showerror("失败", "无法获取支付链接")
        return None

    def cancel_order(self, order_id):
        """取消订单。"""
        url = f"{self.api_client.base_url}/api/AbortOrder.do"
        headers = self.api_client.get_api_headers(f"order.do?order_id={order_id}")
        param = {"orderID": order_id, "studentID": self.api_client.student_info.get('studentID')}
        
        response = self.api_client.api_request("POST", url, event_type="CANCEL_ORDER", json=param, headers=headers, timeout=10)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                messagebox.showinfo("成功", "订单已成功取消!")
                return True
            else:
                messagebox.showerror("失败", result.get("errorMsg", "取消订单失败"))
        return False

    def show_payment_confirmation(self, payment_type, callback):
        """显示支付确认界面，包含免责声明和强制阅读时间。"""
        confirmation_window = tk.Toplevel(self.root)
        confirmation_window.title("支付确认")
        confirmation_window.geometry("600x500")
        confirmation_window.transient(self.root)
        confirmation_window.grab_set()
        confirmation_window.resizable(False, False)
        
        confirmation_window.update_idletasks()
        x = (confirmation_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (confirmation_window.winfo_screenheight() // 2) - (500 // 2)
        confirmation_window.geometry(f"600x500+{x}+{y}")

        main_frame = ttk.Frame(confirmation_window, padding=20)
        main_frame.pack(fill="both", expand=True)

        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        payment_name = "支付宝" if payment_type == "alipay" else "微信"
        title_label = ttk.Label(main_frame, text=f"{payment_name}支付确认", style="Title.TLabel")
        title_label.grid(row=0, column=0, pady=(0, 20), sticky='n')

        disclaimer_text = """重要提示和免责声明

请在继续支付前仔细阅读以下重要信息:

1. 支付安全说明
   • 本软件仅作为新华传媒教材征订平台的客户端工具
   • 所有支付流程均直接对接新华传媒官方支付系统
   • 软件制作者不参与任何资金流转过程

2. 资金流向说明
   • 您的付款将直接支付给:上海新华传媒连锁有限公司
   • 软件制作者不经手、不代收任何费用
   • 本软件仅转发官方网站的支付二维码图片

3. 免责声明
   • 软件制作者对支付过程中可能出现的问题不承担责任
   • 如遇支付纠纷,请直接联系新华传媒官方客服
   • 建议您保留支付凭证以备查询

4. 使用建议
   • 请确认订单信息无误后再进行支付
   • 支付时请使用安全的网络环境
   • 如有疑问请联系新华传媒官方客服

点击"我已阅读并同意"按钮将跳转到支付界面。"""

        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 20))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 10), 
                             state=tk.DISABLED, bg="#f8f9fa", relief="solid", borderwidth=1)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        text_widget.config(state=tk.NORMAL)
        text_widget.insert("1.0", disclaimer_text)
        text_widget.config(state=tk.DISABLED)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky='sew')
        button_frame.grid_columnconfigure(1, weight=1)

        countdown_var = tk.StringVar()
        countdown_label = ttk.Label(button_frame, textvariable=countdown_var, style="Info.TLabel")
        countdown_label.grid(row=0, column=0, sticky='w', padx=(0, 10))

        button_container = ttk.Frame(button_frame)
        button_container.grid(row=0, column=1, sticky='e')

        agree_button = ttk.Button(button_container, text="我已阅读并同意", 
                                 command=lambda: self._on_payment_confirm(confirmation_window, callback),
                                 state="disabled", style="Accent.TButton")
        agree_button.pack(side="right", padx=(10, 0))

        cancel_button = ttk.Button(button_container, text="取消", 
                                  command=confirmation_window.destroy)
        cancel_button.pack(side="right")

        countdown_seconds = [5]

        def update_countdown():
            if not confirmation_window.winfo_exists(): return
            if countdown_seconds[0] > 0:
                countdown_var.set(f"请仔细阅读上述内容,{countdown_seconds[0]}秒后可继续")
                countdown_seconds[0] -= 1
                confirmation_window.after(1000, update_countdown)
            else:
                countdown_var.set("您现在可以继续支付")
                agree_button.config(state="normal")

        update_countdown()

    def _on_payment_confirm(self, window, callback):
        """确认支付后的回调"""
        window.destroy()
        callback()

    # endregion