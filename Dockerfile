FROM python:3.11

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --upgrade pip
RUN pip install uv
RUN uv sync --no-cache
RUN pip install uvicorn

COPY . .

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "dataviz_backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
