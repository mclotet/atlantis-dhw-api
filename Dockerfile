FROM python:3.12-slim

WORKDIR /app

# Install atlantis-core from the submodule (same pattern as atlantis-forge)
COPY libs/atlantis-core/python /tmp/atlantis-core
RUN pip install --no-cache-dir /tmp/atlantis-core[config]

# Install the dhw-api package and its remaining dependencies
COPY pyproject.toml atlantis.toml ./
COPY app/ ./app/
RUN pip install --no-cache-dir .

CMD ["uvicorn", "app.adapters.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
