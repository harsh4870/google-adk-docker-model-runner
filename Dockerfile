FROM python:3.12-slim
WORKDIR /agents

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY agents/ .

EXPOSE 8000

CMD ["bash", "-c", "adk web --host=0.0.0.0"]