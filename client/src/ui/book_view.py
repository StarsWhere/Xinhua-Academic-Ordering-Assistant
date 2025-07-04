# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

def create_book_selection_view(app):
    """
    创建并显示教材选购的主界面。
    :param app: 主ISBNApp实例。
    """
    from .base_view import clear_frame

    clear_frame(app.root)
    main_frame = ttk.Frame(app.root, padding="10")
    main_frame.grid(row=0, column=0, sticky='nsew')
    app.root.grid_rowconfigure(0, weight=1)
    app.root.grid_columnconfigure(0, weight=1)

    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    app.book_widgets = {}

    # --- 内部函数 ---
    def load_book_list():
        # 清理旧组件
        for widget in books_frame.winfo_children():
            widget.destroy()
        app.book_widgets.clear()
        
        url = f"{app.api_client.base_url}/api/GetBookList.do"
        headers = app.api_client.get_api_headers("myBook.do")
        param = {"studentID": app.api_client.student_info.get('studentID')}
        
        response = app.api_client.api_request("POST", url, event_type="GET_BOOK_LIST", json=param, headers=headers, timeout=10)
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get("code") == "0":
                app.all_books_data = result.get("data", [])
                if app.all_books_data:
                    create_book_cards(app.all_books_data)
                else:
                    ttk.Label(books_frame, text="暂无可订购教材", style='Info.TLabel').pack(pady=50)
            else:
                messagebox.showerror("失败", result.get("errorMsg", "获取教材列表失败"))
        update_selection_info()

    def create_book_cards(books_data):
        # ... (此部分逻辑与原文件相同)
        for i, book in enumerate(books_data):
            book_id = book.get("bookID")
            var = tk.BooleanVar(value=False)
            app.book_widgets[book_id] = {'var': var, 'data': book}
            
            card_frame = ttk.Frame(books_frame, borderwidth=1, relief="solid", padding=0)
            card_frame.pack(fill='x', padx=5, pady=5)
            
            # 使用闭包来捕获正确的book_id
            def make_toggle_func(b_id):
                return lambda event: toggle_selection(event, b_id)
            
            toggle_func = make_toggle_func(book_id)

            check_frame = ttk.Frame(card_frame, padding=10)
            check_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,5))
            
            def make_command_func(b_id):
                return lambda: (update_card_style(b_id), update_selection_info())
                
            checkbox = ttk.Checkbutton(check_frame, variable=var, command=make_command_func(book_id))
            checkbox.pack(expand=True)
            
            info_frame = ttk.Frame(card_frame, padding=(10, 5))
            info_frame.pack(side=tk.LEFT, fill='x', expand=True)

            ttk.Label(info_frame, text=f"{book.get('bookName', 'N/A')}", font=('微软雅黑', 11, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text=f"课程: {book.get('course', 'N/A')} ({book.get('courseNo', 'N/A')})", style='Info.TLabel').pack(anchor='w')
            ttk.Label(info_frame, text=f"教师: {book.get('teacher', 'N/A')}  |  课序号: {book.get('classNo', 'N/A')}", style='Info.TLabel').pack(anchor='w')

            price_stock_frame = ttk.Frame(card_frame, padding=10)
            price_stock_frame.pack(side=tk.RIGHT, fill=tk.Y)
            
            real_price = book.get('realPrice', 0)
            ttk.Label(price_stock_frame, text=f"¥{real_price:.2f}", style='Price.TLabel').pack(anchor='e')
            
            stock = book.get('stock', 0)
            stock_text, stock_color = (f"库存: {stock}", "green") if stock > 10 else ((f"仅剩: {stock}", "orange") if stock > 0 else ("缺货", "red"))
            ttk.Label(price_stock_frame, text=stock_text, foreground=stock_color).pack(anchor='e')

            # 绑定点击事件到所有子组件
            for widget in [card_frame, check_frame, info_frame, price_stock_frame] + info_frame.winfo_children() + price_stock_frame.winfo_children():
                widget.bind("<Button-1>", toggle_func)
        
        books_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def toggle_selection(event, b_id):
        current_state = app.book_widgets[b_id]['var'].get()
        app.book_widgets[b_id]['var'].set(not current_state)
        update_card_style(b_id)
        update_selection_info()

    def update_card_style(b_id):
        var = app.book_widgets[b_id]['var']
        card_frame_index = list(app.book_widgets.keys()).index(b_id)
        card_frame = books_frame.winfo_children()[card_frame_index]
        if var.get():
            card_frame.config(style="Selected.TFrame")
        else:
            card_frame.config(style="TFrame")

    def update_selection_info():
        # ... (此部分逻辑与原文件相同)
        count = 0
        total_price = 0.0
        for book_id, info in app.book_widgets.items():
            if info['var'].get():
                count += 1
                total_price += info['data'].get('realPrice', 0)
        selection_info_label.config(text=f"已选择 {count} 本教材，总计：¥{total_price:.2f}")
    
    def select_all_books():
        for book_id in app.book_widgets:
            app.book_widgets[book_id]['var'].set(True)
            update_card_style(book_id)
        update_selection_info()

    def clear_selection():
        for book_id in app.book_widgets:
            app.book_widgets[book_id]['var'].set(False)
            update_card_style(book_id)
        update_selection_info()
    
    def place_order():
        app.place_order() # 回调主应用的下单方法
        
    def export_book_data():
        # ... (此部分逻辑与原文件相同)
        if not app.all_books_data:
            messagebox.showwarning("导出失败", "没有教材数据可导出！")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path: return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                headers = ["课程号", "课程", "课序号", "任课老师", "书名", "定价", "折后价", "库存"]
                writer.writerow(headers)
                for book in app.all_books_data:
                    writer.writerow([
                        book.get("courseNo", ""), book.get("course", ""), book.get("classNo", ""),
                        book.get("teacher", ""), book.get("bookName", ""), f"¥{book.get('price', 0):.2f}",
                        f"¥{book.get('realPrice', 0):.2f}", book.get("stock", "")
                    ])
            messagebox.showinfo("成功", f"教材信息已导出到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出文件时发生错误: {e}")
            
    # --- UI 绘制 ---
    # 顶部信息栏
    top_frame = ttk.Frame(main_frame)
    top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    user_info = f"欢迎您, {app.api_client.student_info.get('studentName', '')} ({app.api_client.student_info.get('studentNo', '')})"
    ttk.Label(top_frame, text=user_info, style='Header.TLabel').pack(side=tk.LEFT, anchor="w")
    
    action_frame = ttk.Frame(top_frame)
    action_frame.pack(side=tk.RIGHT)
    ttk.Button(action_frame, text="刷新列表", command=load_book_list).pack(side=tk.LEFT, padx=5)
    ttk.Button(action_frame, text="导出列表", command=export_book_data).pack(side=tk.LEFT, padx=5)
    ttk.Button(action_frame, text="历史订单", command=app.show_order_history_page).pack(side=tk.LEFT, padx=5)
    ttk.Button(action_frame, text="登出", command=app.logout).pack(side=tk.LEFT, padx=5)
    
    # 卡片式教材列表区域
    list_container = ttk.LabelFrame(main_frame, text="可订购教材")
    list_container.grid(row=1, column=0, sticky="nsew")
    list_container.grid_rowconfigure(0, weight=1)
    list_container.grid_columnconfigure(0, weight=1)
    
    canvas = tk.Canvas(list_container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
    books_frame = ttk.Frame(canvas, padding=5)
    
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    canvas_window = canvas.create_window((0, 0), window=books_frame, anchor="nw")
    
    books_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
    # 底部操作栏
    bottom_frame = ttk.Frame(main_frame, padding=(0, 10))
    bottom_frame.grid(row=2, column=0, sticky="ew")
    
    selection_info_label = ttk.Label(bottom_frame, text="已选择 0 本教材，总计：¥0.00", style='Info.TLabel')
    selection_info_label.pack(side=tk.LEFT, anchor="w")
    
    purchase_frame = ttk.Frame(bottom_frame)
    purchase_frame.pack(side=tk.RIGHT)
    ttk.Button(purchase_frame, text="全选", command=select_all_books).pack(side=tk.LEFT, padx=5)
    ttk.Button(purchase_frame, text="清空", command=clear_selection).pack(side=tk.LEFT, padx=5)
    ttk.Button(purchase_frame, text="订购所选教材", command=place_order, style="Accent.TButton").pack(side=tk.LEFT, padx=5, ipady=5)
    
    load_book_list()