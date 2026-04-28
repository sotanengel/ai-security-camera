FROM python:3.12-slim-bookworm

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip -i https://pypi.org/simple

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir -i https://pypi.org/simple .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "ai_security_camera.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
