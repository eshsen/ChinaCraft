FROM python:3.11-slim

WORKDIR /app

COPY ml-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ml-service ./ml-service
COPY SQL ./SQL

ENV MODEL_DIR=/app/Model
ENV HANZI_DICTIONARY_PATH=/app/SQL/hanzi_with_translations.json
EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "ml-service", "--host", "0.0.0.0", "--port", "8000"]
