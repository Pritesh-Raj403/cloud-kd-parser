FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir boto3==1.35.36 requests==2.32.3
COPY worker/ /app/worker/
COPY prompts/ /app/prompts/
CMD ["python", "worker/worker.py"]
