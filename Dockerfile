FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml atlantis.toml ./
COPY libs/atlantis-core/python ./libs/atlantis-core/python

RUN pip install --no-cache-dir ./libs/atlantis-core/python[config] && \
    pip install --no-cache-dir --no-deps .

COPY app/ ./app/

CMD ["uvicorn", "app.adapters.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
