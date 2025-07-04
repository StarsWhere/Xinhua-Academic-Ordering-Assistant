import tkinter as tk
from tkinter import ttk

def clear_frame(frame):
    """销毁指定框架下的所有子组件。"""
    for widget in frame.winfo_children():
        widget.destroy()

def create_centered_content_frame(root):
    """
    创建一个占据整个窗口的基础框架，并返回一个位于其中央的、用于放置实际内容的子框架。
    """
    clear_frame(root)
    
    base_frame = ttk.Frame(root, padding=0)
    base_frame.grid(row=0, column=0, sticky='nsew')
    
    base_frame.grid_rowconfigure(0, weight=1)
    base_frame.grid_columnconfigure(0, weight=1)
    
    content_container = ttk.Frame(base_frame)
    content_container.grid(row=0, column=0)
    
    return content_container

def setup_styles():
    """配置应用程序的全局UI样式。"""
    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure('Title.TLabel', font=('微软雅黑', 18, 'bold'), padding=(0, 10, 0, 10))
    style.configure('Header.TLabel', font=('微软雅黑', 12, 'bold'))
    style.configure('Info.TLabel', font=('微软雅黑', 10))
    style.configure('Price.TLabel', font=('微软雅黑', 12, 'bold'), foreground='#c0392b')
    style.configure('Success.TLabel', font=('微软雅黑', 12), foreground='green')
    style.configure('Error.TLabel', font=('微软雅黑', 12), foreground='red')
    style.configure('TButton', font=('微软雅黑', 10))
    style.configure('TCheckbutton', font=('微软雅黑', 10))
    style.configure('TLabel', font=('微软雅黑', 10))
    style.configure('TEntry', font=('微软雅黑', 10))
    style.configure('TLabelframe', font=('微软雅黑', 11), padding=10)
    style.configure('TLabelframe.Label', font=('微软雅黑', 11, 'bold'))
    style.configure('Treeview', font=('微软雅黑', 10), rowheight=28)
    style.configure('Treeview.Heading', font=('微软雅黑', 10, 'bold'))
    style.configure("Accent.TButton", font=('微软雅黑', 10, 'bold'), foreground="white", background="#3498db")
    style.configure("Selected.TFrame", background="#eaf6ff")
    style.configure("TFrame", background=style.lookup('TLabel', 'background'))