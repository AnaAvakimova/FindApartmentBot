FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY src/main.py src/menu.py  /app/

ENTRYPOINT ["python3", "-u", "main.py"]