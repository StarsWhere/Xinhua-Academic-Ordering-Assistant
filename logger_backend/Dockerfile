# [修改] 将基础镜像从 3.9-slim 升级到 3.10-slim 或 3.11-slim
FROM python:3.10-slim 
# 或者 python:3.11-slim, 推荐使用较新版本

WORKDIR /code

COPY ./app/requirements.txt /code/requirements.txt

# 添加 --break-system-packages 参数以兼容某些新版pip的行为，虽然在slim镜像中可能不是必需的，但加上更保险
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt --break-system-packages

COPY ./app /code/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]