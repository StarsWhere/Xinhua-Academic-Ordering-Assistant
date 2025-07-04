FROM python:3.10-slim 

WORKDIR /code

COPY ./app/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt --break-system-packages

COPY ./app /code/app

COPY version_info.json /code/version_info.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]