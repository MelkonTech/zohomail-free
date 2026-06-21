FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY pyproject.toml .
COPY zohomail/ zohomail/

RUN pip install --no-cache-dir ".[all]" 2>/dev/null || pip install --no-cache-dir .
RUN playwright install chromium

EXPOSE 8000

CMD ["zohomail-api"]
