from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch
from torch import nn


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE_PATH = PROJECT_ROOT / "Model" / "reference_embeddings.pt"
DEFAULT_DICTIONARY_PATH = PROJECT_ROOT / "SQL" / "hanzi_with_translations.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "SQL" / "hanzi_similarity_game_pairs.json"


def torch_load(path: Path) -> Any:
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def load_dictionary(path: Path) -> dict[str, dict[str, Any]]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    by_char: dict[str, dict[str, Any]] = {}
    for entry in entries:
        char = str(entry.get("char", "")).strip()
        translation = str(entry.get("translation_ru", "")).strip()
        pinyin = entry.get("pinyin") or []
        if isinstance(pinyin, str):
            pinyin = [pinyin]
        pinyin = [str(value).strip() for value in pinyin if str(value).strip()]
        if char and translation and pinyin:
            by_char[char] = {
                "char": char,
                "pinyin": pinyin,
                "translation_ru": translation,
                "strokes": entry.get("strokes"),
                "hsk_level": entry.get("hsk_level"),
            }
    return by_char


def load_prototypes(reference: dict[str, Any], class_count: int) -> torch.Tensor:
    if "class_prototypes" in reference:
        prototypes = reference["class_prototypes"].float()
    elif "image_embeddings" in reference and "image_labels" in reference:
        embeddings = reference["image_embeddings"].float()
        labels = reference["image_labels"]
        items = []
        for label in range(class_count):
            vectors = embeddings[labels == label]
            if vectors.numel() == 0:
                raise RuntimeError(f"No embeddings for class {label}.")
            items.append(nn.functional.normalize(vectors.mean(dim=0), p=2, dim=0))
        prototypes = torch.stack(items)
    else:
        raise RuntimeError("Reference file has no class_prototypes or image embeddings.")

    return nn.functional.normalize(prototypes, p=2, dim=1)


def distinct_game_labels(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_translation = str(left.get("translation_ru", "")).strip().lower()
    right_translation = str(right.get("translation_ru", "")).strip().lower()
    left_pinyin = ", ".join(left.get("pinyin") or []).strip().lower()
    right_pinyin = ", ".join(right.get("pinyin") or []).strip().lower()
    return left_translation != right_translation and left_pinyin != right_pinyin


def build_pairs(
    classes: list[str],
    prototypes: torch.Tensor,
    dictionary: dict[str, dict[str, Any]],
    neighbors_per_char: int,
    max_pairs: int,
) -> list[dict[str, Any]]:
    scores = prototypes @ prototypes.T
    seen: set[tuple[str, str]] = set()
    pairs: list[dict[str, Any]] = []

    for index, char in enumerate(classes):
        left = dictionary.get(char)
        if not left:
            continue

        ranked = torch.argsort(scores[index], descending=True).tolist()
        added_for_char = 0
        for neighbor_index in ranked:
            if neighbor_index == index:
                continue
            right_char = classes[neighbor_index]
            right = dictionary.get(right_char)
            if not right or not distinct_game_labels(left, right):
                continue

            key = tuple(sorted((char, right_char)))
            if key in seen:
                continue

            seen.add(key)
            pairs.append(
                {
                    "id": f"{char}-{right_char}",
                    "similarity": round(float(scores[index, neighbor_index].item()), 6),
                    "left": left,
                    "right": right,
                }
            )
            added_for_char += 1
            if added_for_char >= neighbors_per_char or len(pairs) >= max_pairs:
                break

        if len(pairs) >= max_pairs:
            break

    pairs.sort(key=lambda item: item["similarity"], reverse=True)
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static Hanzi matching-game pairs.")
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE_PATH)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--neighbors-per-char", type=int, default=2)
    parser.add_argument("--max-pairs", type=int, default=5000)
    args = parser.parse_args()

    reference = torch_load(args.reference.expanduser().resolve())
    classes = [str(item) for item in reference["classes"]]
    prototypes = load_prototypes(reference, len(classes))
    dictionary = load_dictionary(args.dictionary.expanduser().resolve())
    pairs = build_pairs(classes, prototypes, dictionary, args.neighbors_per_char, args.max_pairs)

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "source": {
                    "reference": str(args.reference),
                    "dictionary": str(args.dictionary),
                },
                "pair_count": len(pairs),
                "pairs": pairs,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(pairs)} pairs to {output}")


if __name__ == "__main__":
    main()
