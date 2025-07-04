import json
import os
import base64
import logging

class AppSettings:
    """管理应用程序的用户设置，如登录凭据和数据收集偏好。"""
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.defaults = {
            "username": "",
            "encrypted_password": "",
            "save_credentials": True,
            "allow_data_collection": True
        }
        self.settings = self.defaults.copy()
        self.load()

    def load(self):
        """从JSON文件加载设置。如果文件不存在或损坏，则使用默认设置。"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"加载配置文件 '{self.settings_file}' 失败: {e}。将使用默认设置。")
                self.settings = self.defaults.copy()

    def save(self):
        """将当前设置保存到JSON文件。"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"保存设置失败: {e}")

    def get(self, key):
        """获取指定键的设置值。"""
        return self.settings.get(key, self.defaults.get(key))

    def set(self, key, value):
        """设置指定键的值。"""
        self.settings[key] = value
        
    def get_decrypted_password(self):
        """获取解密后的密码。"""
        encrypted = self.get("encrypted_password")
        if not encrypted:
            return ""
        try:
            return base64.b64decode(encrypted.encode('utf-8')).decode('utf-8')
        except Exception:
            return ""

    def set_encrypted_password(self, password):
        """设置加密后的密码。"""
        if not password:
            self.set("encrypted_password", "")
            return
        encrypted = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        self.set("encrypted_password", encrypted)