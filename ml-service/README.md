# ChinaCraft ML service

FastAPI service for Hanzi similarity search. It expects the trained ArcFace artifacts in `../Model`:

- `resnet18_arcface_best.pt`
- `reference_embeddings.pt`

Run locally from the repository root:

```bash
pip install -r ml-service/requirements.txt
uvicorn main:app --app-dir ml-service --host 127.0.0.1 --port 8000
```

Useful environment variables:

- `MODEL_DIR` points to the folder with model artifacts.
- `MODEL_CHECKPOINT` overrides the checkpoint path.
- `REFERENCE_EMBEDDINGS` overrides the reference embeddings path.
- `HANZI_DICTIONARY_PATH` points to `hanzi_with_translations.json`.
