FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY . /app

EXPOSE 8081
CMD ["python", "sentinel_qa_agent.py", "serve", "--host", "0.0.0.0", "--port", "8081"]
