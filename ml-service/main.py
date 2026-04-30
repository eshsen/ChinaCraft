from __future__ import annotations

import json
import os
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from PIL import Image
from torch import nn
from torchvision import models, transforms


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "Model"
DEFAULT_DICTIONARY_PATH = PROJECT_ROOT / "SQL" / "hanzi_with_translations.json"


class ResNet18Embedder(nn.Module):
    def __init__(self, embedding_dim: int) -> None:
        super().__init__()
        self.backbone = models.resnet18(weights=None)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Linear(in_features, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedding = self.backbone(x)
        return nn.functional.normalize(embedding, p=2, dim=1)


def torch_load(path: Path, map_location: str | torch.device) -> Any:
    try:
        return torch.load(path, map_location=map_location, weights_only=False)
    except TypeError:
        return torch.load(path, map_location=map_location)


def normalize_pinyin(value: str) -> str:
    return (
        unicodedata.normalize("NFD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .strip()
    )


def build_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )


def load_dictionary(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}

    entries = json.loads(path.read_text(encoding="utf-8"))
    by_char: dict[str, dict[str, Any]] = {}
    for entry in entries:
        char = str(entry.get("char", "")).strip()
        if char:
            by_char[char] = entry
        traditional = str(entry.get("traditional", "")).strip()
        if traditional and traditional not in by_char:
            by_char[traditional] = entry
    return by_char


def to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class HanziSearchService:
    def __init__(self) -> None:
        model_dir = Path(os.environ.get("MODEL_DIR", DEFAULT_MODEL_DIR)).resolve()
        dictionary_path = Path(
            os.environ.get("HANZI_DICTIONARY_PATH", DEFAULT_DICTIONARY_PATH)
        ).resolve()
        checkpoint_path = Path(
            os.environ.get("MODEL_CHECKPOINT", model_dir / "resnet18_arcface_best.pt")
        ).resolve()
        reference_path = Path(
            os.environ.get("REFERENCE_EMBEDDINGS", model_dir / "reference_embeddings.pt")
        ).resolve()

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        if not reference_path.exists():
            raise FileNotFoundError(f"Reference embeddings not found: {reference_path}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.checkpoint_path = checkpoint_path
        self.reference_path = reference_path
        self.transform = build_transform()
        self.metadata = load_dictionary(dictionary_path)

        checkpoint = torch_load(checkpoint_path, map_location="cpu")
        self.classes = [str(item) for item in checkpoint["classes"]]
        self.class_to_index = {char: idx for idx, char in enumerate(self.classes)}

        self.model = ResNet18Embedder(int(checkpoint["embedding_dim"]))
        self.model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        self.model = self.model.to(self.device)
        self.model.eval()

        reference = torch_load(reference_path, map_location="cpu")
        reference_classes = [str(item) for item in reference.get("classes", self.classes)]
        if reference_classes != self.classes:
            raise RuntimeError("Reference classes do not match checkpoint classes.")

        self.prototypes = self._load_prototypes(reference).to(self.device)
        self.sample_paths = [
            str(path) for path in reference.get("class_sample_paths", [""] * len(self.classes))
        ]

    def _load_prototypes(self, reference: dict[str, Any]) -> torch.Tensor:
        if "class_prototypes" in reference:
            prototypes = reference["class_prototypes"].float()
        elif "image_embeddings" in reference and "image_labels" in reference:
            embeddings = reference["image_embeddings"].float()
            labels = reference["image_labels"]
            prototypes = []
            for label in range(len(self.classes)):
                mask = labels == label
                vectors = embeddings[mask]
                if vectors.numel() == 0:
                    raise RuntimeError(f"No reference embeddings for class {label}.")
                prototypes.append(nn.functional.normalize(vectors.mean(dim=0), p=2, dim=0))
            prototypes = torch.stack(prototypes)
        else:
            raise RuntimeError("Reference embeddings file has no usable prototype data.")

        return nn.functional.normalize(prototypes, p=2, dim=1)

    @torch.inference_mode()
    def search_image(
        self,
        image: Image.Image,
        top_k: int,
        hsk_level: int | None,
        strokes_min: int | None,
        strokes_max: int | None,
    ) -> dict[str, Any]:
        tensor = self.transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        query_vector = self.model(tensor).squeeze(0)
        candidates = self._rank(query_vector, top_k, hsk_level, strokes_min, strokes_max)
        return self._response("image", "image", top_k, candidates)

    def search_text(
        self,
        query: str,
        top_k: int,
        hsk_level: int | None,
        strokes_min: int | None,
        strokes_max: int | None,
    ) -> dict[str, Any]:
        seed_indices = self._direct_char_indices(query)
        if seed_indices:
            vectors = self.prototypes[seed_indices]
            query_vector = nn.functional.normalize(vectors.mean(dim=0), p=2, dim=0)
            candidates = self._rank(query_vector, top_k, hsk_level, strokes_min, strokes_max)
            return self._response(query, "text", top_k, candidates)

        pinyin_matches = self._pinyin_matches(query)
        candidates: list[dict[str, Any]] = []
        for idx, score in pinyin_matches:
            meta = self.metadata.get(self.classes[idx], {})
            if not self._passes_filters(meta, hsk_level, strokes_min, strokes_max):
                continue
            candidates.append(self._candidate(idx, score))
            if len(candidates) >= top_k:
                break

        return self._response(query, "text", top_k, candidates)

    def _direct_char_indices(self, query: str) -> list[int]:
        q = query.strip()
        if not q:
            return []

        direct_matches = []
        for char in q:
            if char in self.class_to_index:
                direct_matches.append(self.class_to_index[char])
        return list(dict.fromkeys(direct_matches))

    def _pinyin_matches(self, query: str) -> list[tuple[int, float]]:
        q = query.strip()
        if not q:
            return []
        normalized_query = normalize_pinyin(q)
        exact: list[tuple[int, float]] = []
        contains: list[tuple[int, float]] = []
        for char, entry in self.metadata.items():
            idx = self.class_to_index.get(char)
            if idx is None:
                continue
            pinyin_values = entry.get("pinyin") or []
            if isinstance(pinyin_values, str):
                pinyin_values = [pinyin_values]
            normalized_values = [normalize_pinyin(str(value)) for value in pinyin_values]
            if normalized_query in normalized_values:
                exact.append((idx, 1.0))
            elif any(normalized_query in value for value in normalized_values):
                contains.append((idx, 0.8))

        deduped: dict[int, float] = {}
        for idx, score in exact + contains:
            deduped.setdefault(idx, score)
        return list(deduped.items())

    def _rank(
        self,
        query_vector: torch.Tensor,
        top_k: int,
        hsk_level: int | None,
        strokes_min: int | None,
        strokes_max: int | None,
    ) -> list[dict[str, Any]]:
        scores = torch.mv(self.prototypes, query_vector)
        ranked = torch.argsort(scores, descending=True).tolist()

        candidates: list[dict[str, Any]] = []
        for idx in ranked:
            char = self.classes[idx]
            meta = self.metadata.get(char, {})
            if not self._passes_filters(meta, hsk_level, strokes_min, strokes_max):
                continue

            score = max(0.0, min(1.0, float(scores[idx].item())))
            candidates.append(self._candidate(idx, score))
            if len(candidates) >= top_k:
                break

        return candidates

    def _candidate(self, idx: int, score: float) -> dict[str, Any]:
        char = self.classes[idx]
        meta = self.metadata.get(char, {})
        pinyin = meta.get("pinyin") or []
        if isinstance(pinyin, str):
            pinyin = [pinyin]

        return {
            "char": char,
            "score": round(max(0.0, min(1.0, score)), 6),
            "pinyin": pinyin,
            "hsk_level": to_int(meta.get("hsk_level")),
            "strokes": to_int(meta.get("strokes")),
            "translation_ru": meta.get("translation_ru", ""),
            "sample_image": self.sample_paths[idx] if idx < len(self.sample_paths) else "",
        }

    @staticmethod
    def _passes_filters(
        meta: dict[str, Any],
        hsk_level: int | None,
        strokes_min: int | None,
        strokes_max: int | None,
    ) -> bool:
        meta_hsk_level = to_int(meta.get("hsk_level"))
        if hsk_level is not None and meta_hsk_level != hsk_level:
            return False
        strokes = to_int(meta.get("strokes"))
        if strokes_min is not None and (strokes is None or strokes < strokes_min):
            return False
        if strokes_max is not None and (strokes is None or strokes > strokes_max):
            return False
        return True

    def _response(
        self,
        query: str,
        query_type: str,
        top_k: int,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "query": query,
            "query_type": query_type,
            "top_k": top_k,
            "model_version": self.checkpoint_path.name,
            "index_version": self.reference_path.name,
            "candidates": candidates,
        }


@lru_cache(maxsize=1)
def get_service() -> HanziSearchService:
    return HanziSearchService()


app = FastAPI(title="ChinaCraft Hanzi similarity service")


@app.get("/health")
def health() -> dict[str, Any]:
    service = get_service()
    return {
        "ok": True,
        "device": str(service.device),
        "classes": len(service.classes),
        "model": service.checkpoint_path.name,
        "index": service.reference_path.name,
    }


@app.post("/search/by-image")
async def search_by_image(
    image: UploadFile = File(...),
    top_k: int = Query(10, ge=1, le=50),
    hsk_level: int | None = Query(None, ge=1, le=6),
    strokes_min: int | None = Query(None, ge=1),
    strokes_max: int | None = Query(None, ge=1),
) -> dict[str, Any]:
    try:
        pil_image = Image.open(image.file).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file.") from exc

    service = get_service()
    return service.search_image(pil_image, top_k, hsk_level, strokes_min, strokes_max)


@app.get("/search/by-text")
def search_by_text(
    q: str = Query(..., min_length=1),
    top_k: int = Query(10, ge=1, le=50),
    hsk_level: int | None = Query(None, ge=1, le=6),
    strokes_min: int | None = Query(None, ge=1),
    strokes_max: int | None = Query(None, ge=1),
) -> dict[str, Any]:
    service = get_service()
    return service.search_text(q, top_k, hsk_level, strokes_min, strokes_max)
