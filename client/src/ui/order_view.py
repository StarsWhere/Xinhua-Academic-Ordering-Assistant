# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from io import BytesIO
from urllib.parse import quote
import threading

def create_order_history_view(app):
    """创建并显示历史订单列表界面。"""
    from .base_view import clear_frame

    clear_frame(app.root)
    main_frame = ttk.Frame(app.root, padding="10")
    main_frame.grid(row=0, column=0, sticky='nsew')
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    def load_order_history():
        for i in order_history_tree.get_children(): order_history_tree.delete(i)
        
        url = f"{app.api_client.base_url}/api/GetOrderList.do"
        headers = app.api_client.get_api_headers("myOrder.do")
        param = {"studentID": app.api_client.student_info.get('studentID'), "historySign": "100"}
        
        response = app.api_client.api_request("POST", url, event_type="GET_ORDER_HISTORY", json=param, headers=headers, timeout=10)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                for order in result.get("data", []):
                    order_history_tree.insert("", tk.END, values=(
                        order.get("orderID", ""), f"¥{order.get('amount', 0):.2f}",
                        order.get("status", ""), order.get("orderDate", ""),
                        order.get("payType", "")
                    ))
            else:
                messagebox.showerror("失败", result.get("errorMsg", "获取历史订单失败"))

    def on_order_history_double_click(event):
        item_id = order_history_tree.identify_row(event.y)
        if not item_id: return
        order_id = order_history_tree.item(item_id, 'values')[0]
        app.show_order_detail_page(order_id)

    top_frame = ttk.Frame(main_frame)
    top_frame.grid(row=0, column=0, sticky="ew", pady=(0,10))
    ttk.Label(top_frame, text="历史订单", style='Title.TLabel').pack(side=tk.LEFT)
    ttk.Button(top_frame, text="返回教材选购", command=app.show_book_selection_page).pack(side=tk.RIGHT, padx=5)

    tree_frame = ttk.Frame(main_frame)
    tree_frame.grid(row=1, column=0, sticky="nsew")
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    cols = ("order_id", "amount", "status", "order_time", "pay_method")
    order_history_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    order_history_tree.grid(row=0, column=0, sticky="nsew")
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=order_history_tree.yview)
    order_history_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky="ns")

    for col_name, text in [("order_id", "订单号"), ("amount", "订单金额"), ("status", "状态"), ("order_time", "订购时间"), ("pay_method", "支付方式")]:
        order_history_tree.heading(col_name, text=text)
        order_history_tree.column(col_name, anchor="center")
    order_history_tree.column("order_id", width=200, anchor="w")
    
    order_history_tree.bind("<Double-1>", on_order_history_double_click)
    load_order_history()


def create_order_detail_view(app, order_id):
    """创建并显示单个订单的详情界面,包含内嵌二维码支付功能。"""
    from .base_view import clear_frame

    clear_frame(app.root)
    app.current_order_data = None
    
    main_frame = ttk.Frame(app.root, padding="10")
    main_frame.grid(row=0, column=0, sticky="nsew")
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    
    # --- 内部函数 ---
    def load_order_details():
        for i in order_detail_tree.get_children(): order_detail_tree.delete(i)
        response = app.get_order_details(order_id)
        if response:
            update_order_detail_ui(response)
        else:
             app.show_book_selection_page()

    def update_order_detail_ui(order_data):
        app.current_order_data = order_data
        order_amount_label.config(text=f"订单金额:¥{order_data.get('amount', 0):.2f}")
        order_status_label.config(text=f"状态:{order_data.get('status', '')}")
        order_time_label.config(text=f"订购时间:{order_data.get('orderDate', '')}")
        total_pay_label.config(text=f"您需要支付:¥{order_data.get('amount', 0):.2f}")
        
        for widget in payment_buttons_frame.winfo_children(): widget.destroy()

        if order_data.get('status', '') == '未支付':
            ttk.Button(payment_buttons_frame, text="支付宝支付", 
                      command=lambda: app.show_payment_confirmation("alipay", lambda: show_payment_qr("alipay"))).pack(side=tk.LEFT, padx=5, ipady=5)
            ttk.Button(payment_buttons_frame, text="微信支付", 
                      command=lambda: app.show_payment_confirmation("wechat", lambda: show_payment_qr("wechat"))).pack(side=tk.LEFT, padx=5, ipady=5)
            ttk.Button(payment_buttons_frame, text="取消订单", command=lambda: cancel_order(order_id)).pack(side=tk.LEFT, padx=5, ipady=5)
        else:
            total_pay_label.config(text=f"订单状态: {order_data.get('status', '')}")

        for detail in order_data.get('orderDetails', []):
            order_detail_tree.insert("", tk.END, values=(
                detail.get("bookName", ""), f"¥{detail.get('amount', 0):.2f}",
                detail.get("orderNum", ""), detail.get("payStatusName", ""), detail.get("sendStatusName", "")
            ))

    def show_payment_qr(payment_type):
        data_url = app.get_payment_url(payment_type)
        if not data_url: return
        
        qr_url = f"{app.api_client.base_url}/check/QRCode.do?data={quote(data_url, safe='')}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": app.api_client.base_url}
        
        content_frame.grid_remove()
        qr_code_display_frame.grid()
        
        qr_title_label.config(text=f"{'支付宝' if payment_type == 'alipay' else '微信'}支付")

        def fetch_and_display_qr():
            try:
                response = app.api_client.session.get(qr_url, headers=headers, stream=True, timeout=10)
                if response and response.status_code == 200:
                    original_image = Image.open(BytesIO(response.content))
                    qr_image_label.original_image = original_image
                    qr_code_display_frame.update_idletasks()
                    resize_qr_image() 
                else:
                    messagebox.showerror("错误", "获取支付二维码失败")
                    hide_payment_qr()
            except Exception as e:
                messagebox.showerror("错误", f"加载二维码图片失败: {e}")
                hide_payment_qr()

        threading.Thread(target=fetch_and_display_qr, daemon=True).start()

    def hide_payment_qr():
        qr_code_display_frame.grid_remove()
        content_frame.grid()

    def cancel_order(order_id_to_cancel):
        if messagebox.askyesno("确认取消", "您确定要取消这个订单吗?此操作不可恢复。"):
            if app.cancel_order(order_id_to_cancel):
                load_order_details()

    def refresh_payment_status():
        """刷新支付状态并在当前界面显示结果"""
        status_label.config(text="正在查询支付状态...", style="Info.TLabel")
        
        def do_check():
            order_data = app.get_order_details(order_id)
            if order_data:
                if str(order_data.get('paid')).lower() == 'true' or order_data.get('status') == '已支付':
                    status_label.config(text=f"支付成功! 已支付金额:¥{order_data.get('payAmount', 0):.2f}", style="Success.TLabel")
                    # 延迟2秒后自动返回订单详情并刷新
                    qr_code_display_frame.after(2000, lambda: (hide_payment_qr(), load_order_details()))
                else:
                    status_label.config(text="订单尚未支付，请完成支付后再次刷新", style="Error.TLabel")
            else:
                status_label.config(text="查询失败，请检查网络连接", style="Error.TLabel")

        threading.Thread(target=do_check, daemon=True).start()

    def refresh_qr_code():
        """刷新二维码"""
        current_payment_type = "alipay" if "支付宝" in qr_title_label.cget("text") else "wechat"
        status_label.config(text="正在刷新二维码...", style="Info.TLabel")
        
        def refresh_task():
            data_url = app.get_payment_url(current_payment_type)
            if data_url:
                qr_url = f"{app.api_client.base_url}/check/QRCode.do?data={quote(data_url, safe='')}"
                headers = {"User-Agent": "Mozilla/5.0", "Referer": app.api_client.base_url}
                
                try:
                    response = app.api_client.session.get(qr_url, headers=headers, stream=True, timeout=10)
                    if response and response.status_code == 200:
                        original_image = Image.open(BytesIO(response.content))
                        qr_image_label.original_image = original_image
                        qr_code_display_frame.update_idletasks()
                        resize_qr_image()
                        status_label.config(text="二维码已刷新，请使用新的二维码进行支付", style="Success.TLabel")
                    else:
                        status_label.config(text="刷新二维码失败，请重试", style="Error.TLabel")
                except Exception as e:
                    status_label.config(text=f"刷新失败: {str(e)}", style="Error.TLabel")
            else:
                status_label.config(text="获取支付链接失败", style="Error.TLabel")
        
        threading.Thread(target=refresh_task, daemon=True).start()

    # --- UI 绘制 ---
    # 主内容框架
    content_frame = ttk.Frame(main_frame)
    content_frame.grid(row=0, column=0, sticky='nsew')
    content_frame.grid_rowconfigure(2, weight=1)
    content_frame.grid_columnconfigure(0, weight=1)

    # 二维码显示框架(默认隐藏),负责将内部内容居中
    qr_code_display_frame = ttk.Frame(main_frame)
    qr_code_display_frame.grid(row=0, column=0, sticky='nsew')
    qr_code_display_frame.grid_rowconfigure(0, weight=1)
    qr_code_display_frame.grid_columnconfigure(0, weight=1)
    
    # 包含所有二维码页面控件的内部框架
    qr_inner_frame = ttk.Frame(qr_code_display_frame)
    qr_inner_frame.grid(row=0, column=0) 
    
    qr_title_label = ttk.Label(qr_inner_frame, text="", style="Header.TLabel")
    qr_title_label.grid(row=0, column=0, pady=10)

    payee_label = ttk.Label(qr_inner_frame, text="收款方:上海新华传媒连锁有限公司", font=("", 12))
    payee_label.grid(row=1, column=0, pady=(0, 10))
    
    qr_image_label = ttk.Label(qr_inner_frame)
    qr_image_label.grid(row=2, column=0, sticky='nsew')
    
    # 状态提示标签
    status_label = ttk.Label(qr_inner_frame, text="请使用对应的支付应用扫描上方二维码完成支付", style="Info.TLabel")
    status_label.grid(row=3, column=0, pady=10)
    
    # 二维码页面的按钮组
    qr_buttons_frame = ttk.Frame(qr_inner_frame)
    qr_buttons_frame.grid(row=4, column=0, pady=10)
    
    ttk.Button(qr_buttons_frame, text="刷新支付状态", command=refresh_payment_status, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
    ttk.Button(qr_buttons_frame, text="刷新二维码", command=refresh_qr_code).pack(side=tk.LEFT, padx=5)
    ttk.Button(qr_buttons_frame, text="返回订单详情", command=hide_payment_qr).pack(side=tk.LEFT, padx=5)

    def resize_qr_image(event=None):
        if hasattr(qr_image_label, 'original_image') and qr_image_label.original_image:
            qr_inner_frame.update_idletasks()

            other_widgets_height = (
                qr_title_label.winfo_height() +
                payee_label.winfo_height() +
                status_label.winfo_height() +
                qr_buttons_frame.winfo_height()
            )
            total_padding_y = 10 + 10 + 10 + 10

            container_width = qr_code_display_frame.winfo_width()
            container_height = qr_code_display_frame.winfo_height()

            image_space_w = container_width - 60
            image_space_h = container_height - other_widgets_height - total_padding_y

            if image_space_w <= 1 or image_space_h <= 1:
                return

            original_image = qr_image_label.original_image
            original_width, original_height = original_image.size

            if original_width == 0 or original_height == 0: return

            ratio = min(image_space_w / original_width, image_space_h / original_height)
            
            new_width = max(1, int(original_width * ratio))
            new_height = max(1, int(original_height * ratio))

            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.LANCZOS

            resized_image = original_image.resize((new_width, new_height), resample_filter)
            photo = ImageTk.PhotoImage(resized_image)
            qr_image_label.config(image=photo)
            qr_image_label.image = photo

    qr_code_display_frame.bind('<Configure>', resize_qr_image)
    
    # =================================================================
    # == 核心修复:重新添加对 qr_inner_frame 内部空间的管理规则       ==
    # =================================================================
    qr_inner_frame.grid_columnconfigure(0, weight=1)
    qr_inner_frame.grid_rowconfigure(2, weight=1) # 关键:只让图片所在的第2行扩展

    qr_code_display_frame.grid_remove()

    # -- 主内容UI组件 --
    ttk.Label(content_frame, text=f"订单详情 (订单号: {order_id})", style='Title.TLabel').grid(row=0, column=0, sticky="w")
    
    order_info_panel = ttk.LabelFrame(content_frame, text="订单概览", padding="10")
    order_info_panel.grid(row=1, column=0, sticky="new", pady=10)
    order_amount_label = ttk.Label(order_info_panel, text="订单金额:...")
    order_amount_label.pack(anchor="w")
    order_status_label = ttk.Label(order_info_panel, text="状态:...")
    order_status_label.pack(anchor="w")
    order_time_label = ttk.Label(order_info_panel, text="订购时间:...")
    order_time_label.pack(anchor="w")

    detail_list_frame = ttk.LabelFrame(content_frame, text="包含书目")
    detail_list_frame.grid(row=2, column=0, sticky="nsew", pady=10)
    detail_list_frame.grid_rowconfigure(0, weight=1)
    detail_list_frame.grid_columnconfigure(0, weight=1)
    
    cols = ("book_name", "price", "count", "pay_status", "delivery_status")
    order_detail_tree = ttk.Treeview(detail_list_frame, columns=cols, show="headings")
    order_detail_tree.grid(row=0, column=0, sticky="nsew")
    for col_name, text, width in [("book_name", "书名", 250), ("price", "支付金额", 120), ("count", "订数", 100), ("pay_status", "支付状态", 120), ("delivery_status", "发货状态", 120)]:
        order_detail_tree.heading(col_name, text=text)
        order_detail_tree.column(col_name, anchor="center", width=width)
    order_detail_tree.column("book_name", anchor="w")

    checkout_frame = ttk.LabelFrame(content_frame, text="收银台", padding="10")
    checkout_frame.grid(row=3, column=0, sticky="ew")
    total_pay_label = ttk.Label(checkout_frame, text="您需要支付:¥ ...", style='Header.TLabel')
    total_pay_label.pack(side=tk.LEFT, padx=10)
    payment_buttons_frame = ttk.Frame(checkout_frame)
    payment_buttons_frame.pack(side=tk.RIGHT)

    bottom_nav = ttk.Frame(content_frame, padding=(0, 10))
    bottom_nav.grid(row=4, column=0, sticky="ew", pady=(10, 0))
    ttk.Button(bottom_nav, text="返回教材选购", command=app.show_book_selection_page).pack(side=tk.LEFT, padx=5)
    ttk.Button(bottom_nav, text="查看历史订单", command=app.show_order_history_page).pack(side=tk.LEFT, padx=5)

    load_order_details()