import requests
import logging
import json
from datetime import datetime
import threading

class ApiClient:
    """
    封装所有对新华传媒平台API的请求。
    管理 `requests.Session`，统一处理API请求和响应，并根据用户设置决定是否上报日志。
    """
    def __init__(self, settings):
        self.settings = settings
        self.session = requests.Session()
        self.base_url = "https://univ.xinhua.sh.cn"
        self.base_backend_url = "https://api.school.starswhere.xyz:44" # 数据收集、OCR和版本检查后端地址
        self.student_info = {}

    def get_api_headers(self, referer_path=""):
        """获取通用的API请求头。"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json;charset=utf-8",
            "Origin": self.base_url,
            "Connection": "keep-alive",
            "Referer": f"{self.base_url}/{referer_path}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

    def _log_to_external_api(self, event_type, request_info, response_info=None, error_msg=None):
        """将结构化日志发送到我们自己的后端。"""
        if not self.settings.get("allow_data_collection"):
            logging.info("用户已禁用数据收集,跳过日志上报。")
            return
        
        def task():
            log_data = {
                "event_type": event_type,
                "student_id": self.student_info.get('studentID'),
                "student_no": self.student_info.get('studentNo'),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request": request_info,
                "response": response_info,
                "error": error_msg
            }
            try:
                requests.post(f"{self.base_backend_url}/log", json=log_data, timeout=10)
            except requests.exceptions.RequestException as e:
                logging.error(f"发送日志到API失败: {e}")
        
        threading.Thread(target=task, name="ApiLogThread", daemon=True).start()

    def api_request(self, method, url, event_type="GENERIC_API_CALL", **kwargs):
        """
        统一的API请求封装,自动处理日志记录。
        """
        request_payload = kwargs.get('json', kwargs.get('params', {}))
        response = None
        
        request_info = {
            "method": method, "url": url, "payload": request_payload,
            "headers": {k: v for k, v in self.session.headers.items() if 'Cookie' not in k}
        }
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            response_body = ""
            try:
                response_body = response.json()
            except json.JSONDecodeError:
                response_body = response.text[:2000]
            
            response_info = {
                "status_code": response.status_code, "body": response_body,
                "headers": dict(response.headers)
            }
            self._log_to_external_api(event_type + "_SUCCESS", request_info, response_info)
            return response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API请求失败: {e}")
            
            error_msg = str(e)
            response_info = None
            if e.response is not None:
                try:
                    body = e.response.json()
                except json.JSONDecodeError:
                    body = e.response.text[:2000]
                response_info = {"status_code": e.response.status_code, "body": body}
            
            self._log_to_external_api(event_type + "_FAIL", request_info, response_info, error_msg)
            return e.response if e.response is not None else None

    def send_forget_password_code(self, student_code, mobile_no):
        """为忘记密码功能发送短信验证码。"""
        url = f"{self.base_url}/api/sendCodeAndStudentNo.do"
        params = {"mobile": mobile_no, "studentCode": student_code}
        headers = self.get_api_headers("forgetpwd.do")
        return self.api_request("GET", url, event_type="SEND_FORGET_PWD_CODE", params=params, headers=headers, timeout=10)

    def reset_password(self, student_code, mobile_no, validate_code):
        """重置用户密码。"""
        url = f"{self.base_url}/api/ResetPwd.do"
        params = {"studentCode": student_code, "mobile": mobile_no, "code": validate_code}
        headers = self.get_api_headers("forgetpwd.do")
        return self.api_request("GET", url, event_type="RESET_PASSWORD", params=params, headers=headers, timeout=10)

    def send_bind_phone_code(self, mobile_no):
        """为绑定手机功能发送短信验证码。"""
        url = f"{self.base_url}/api/sendCode.do"
        params = {"mobile": mobile_no}
        headers = self.get_api_headers("setPwd.do")
        return self.api_request("GET", url, event_type="SEND_BIND_PHONE_CODE", params=params, headers=headers, timeout=10)

    def bind_phone(self, mobile_no, validate_code):
        """绑定手机号到当前账户。"""
        url = f"{self.base_url}/api/bindPhone.do"
        params = {"mobile": mobile_no, "code": validate_code}
        headers = self.get_api_headers("setPwd.do")
        return self.api_request("GET", url, event_type="BIND_PHONE", params=params, headers=headers, timeout=10)

    def call_ocr_service(self, image_base64: str):
        """
        调用后端OCR服务识别验证码。
        :param image_base64: 验证码图片的base64编码字符串。
        :return: 识别结果字典或None。
        """
        ocr_url = f"{self.base_backend_url}/ocr_captcha"
        headers = {'Content-Type': 'application/json'}
        payload = {"imageBase64": image_base64}
        
        try:
            logging.info(f"正在通过后端代理调用OCR服务: {ocr_url}")
            response = requests.post(ocr_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"调用后端OCR服务失败: {e}")
            return None

    def check_for_updates(self, client_version: str):
        """
        调用后端服务检查是否有新版本。
        :param client_version: 客户端当前版本号。
        :return: 更新信息字典或None。
        """
        version_check_url = f"{self.base_backend_url}/version_check?client_version={client_version}"
        try:
            logging.info(f"正在检查版本更新: {version_check_url}")
            response = requests.get(version_check_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"调用版本检查服务失败: {e}")
            return None