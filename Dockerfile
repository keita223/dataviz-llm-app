FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install uv
RUN uv sync

EXPOSE 7860

CMD ["uvicorn", "dataviz_backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
