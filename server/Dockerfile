FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY server/ server/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "server.api:app", "--host", "0.0.0.0", "--port", "8000"]
