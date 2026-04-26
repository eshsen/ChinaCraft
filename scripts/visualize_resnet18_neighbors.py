from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from PIL import Image, ImageDraw
from torchvision import models, transforms


DEFAULT_DATA_ROOT = (
    Path(__file__).resolve().parents[1]
    / "Dataset"
    / "Traditional-Chinese-Handwriting-Dataset-ready"
    / "by_character"
)
DEFAULT_ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "Dataset"
    / "Traditional-Chinese-Handwriting-Dataset-ready"
    / "resnet18_arcface_artifacts"
)
DEFAULT_CHECKPOINT = DEFAULT_ARTIFACTS_DIR / "resnet18_arcface_best.pt"
IMAGE_EXTENSIONS = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}


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


class ImagePathDataset(Dataset):
    def __init__(self, records: list[tuple[Path, int]], transform: transforms.Compose) -> None:
        self.records = records
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int, str]:
        path, label = self.records[index]
        image = Image.open(path).convert("RGB")
        return self.transform(image), label, str(path)


def build_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )


def collect_records(data_root: Path, classes: list[str], max_images_per_class: int) -> list[tuple[Path, int]]:
    records: list[tuple[Path, int]] = []
    for label, character in enumerate(classes):
        folder = data_root / character
        paths = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS])
        if max_images_per_class > 0:
            paths = paths[:max_images_per_class]
        records.extend((path, label) for path in paths)
    return records


@torch.inference_mode()
def build_reference_embeddings(
    model: nn.Module,
    records: list[tuple[Path, int]],
    classes: list[str],
    batch_size: int,
    num_workers: int,
    device: torch.device,
) -> dict:
    dataset = ImagePathDataset(records, build_transform())
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    all_embeddings: list[torch.Tensor] = []
    all_labels: list[torch.Tensor] = []
    all_paths: list[str] = []

    model.eval()
    for images, labels, paths in loader:
        images = images.to(device)
        embeddings = model(images).cpu()
        all_embeddings.append(embeddings)
        all_labels.append(labels)
        all_paths.extend(paths)

    image_embeddings = torch.cat(all_embeddings, dim=0)
    image_labels = torch.cat(all_labels, dim=0)
    prototypes = []
    sample_paths = []
    for label in range(len(classes)):
        mask = image_labels == label
        vectors = image_embeddings[mask]
        prototype = nn.functional.normalize(vectors.mean(dim=0), p=2, dim=0)
        prototypes.append(prototype)
        label_paths = [path for path, item_label in zip(all_paths, image_labels.tolist()) if item_label == label]
        sample_paths.append(label_paths[0] if label_paths else "")

    return {
        "classes": classes,
        "image_embeddings": image_embeddings,
        "image_labels": image_labels,
        "image_paths": all_paths,
        "class_prototypes": torch.stack(prototypes),
        "class_sample_paths": sample_paths,
    }


def fit_image(path: str, size: int) -> Image.Image:
    try:
        image = Image.open(path).convert("RGB")
    except Exception:
        image = Image.new("RGB", (size, size), color=(245, 245, 245))
    return image.resize((size, size))


def draw_grid(results: list[dict], output_path: Path, cell: int = 120, margin: int = 12) -> None:
    cols = 11
    rows = len(results)
    header = 28
    canvas = Image.new(
        "RGB",
        (cols * cell + (cols + 1) * margin, rows * (cell + header) + (rows + 1) * margin),
        color=(255, 255, 255),
    )
    draw = ImageDraw.Draw(canvas)

    for row, result in enumerate(results):
        y = margin + row * (cell + header + margin)
        query = result["query"]
        x = margin
        canvas.paste(fit_image(query["sample_image"], cell), (x, y + header))
        draw.text((x + 4, y + 4), f"Q: {query['char']}", fill=(180, 0, 0))
        draw.rectangle([x, y + header, x + cell, y + header + cell], outline=(180, 0, 0), width=2)

        for index, item in enumerate(result["neighbors"], start=1):
            x = margin + index * (cell + margin)
            canvas.paste(fit_image(item["sample_image"], cell), (x, y + header))
            draw.text((x + 4, y + 4), f"{index}. {item['char']} {item['score']:.2f}", fill=(20, 20, 20))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Visualize random Hanzi nearest neighbors from ResNet18 embeddings.")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS_DIR)
    parser.add_argument("--num-queries", type=int, default=10)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-images-per-class", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()

    data_root = args.data_root.expanduser().resolve()
    checkpoint_path = args.checkpoint.expanduser().resolve()
    artifacts_dir = args.artifacts_dir.expanduser().resolve()
    index_path = artifacts_dir / "reference_embeddings.pt"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.require_cuda and device.type != "cuda":
        raise RuntimeError("CUDA is required but not available.")

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    classes = checkpoint["classes"]
    model = ResNet18Embedder(int(checkpoint["embedding_dim"]))
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model = model.to(device)

    if index_path.exists() and not args.rebuild_index:
        reference = torch.load(index_path, map_location="cpu")
    else:
        records = collect_records(data_root, classes, args.max_images_per_class)
        reference = build_reference_embeddings(
            model=model,
            records=records,
            classes=classes,
            batch_size=args.batch_size,
            num_workers=args.num_workers,
            device=device,
        )
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        torch.save(reference, index_path)

    prototypes = reference["class_prototypes"]
    sample_paths = reference["class_sample_paths"]
    rng = random.Random(args.seed)
    query_indices = rng.sample(range(len(classes)), k=min(args.num_queries, len(classes)))
    results = []

    for query_index in query_indices:
        scores = torch.mv(prototypes, prototypes[query_index])
        ranked = torch.argsort(scores, descending=True).tolist()
        neighbors = []
        for candidate_index in ranked:
            if candidate_index == query_index:
                continue
            neighbors.append(
                {
                    "char": classes[candidate_index],
                    "score": round(float(scores[candidate_index].item()), 6),
                    "sample_image": sample_paths[candidate_index],
                }
            )
            if len(neighbors) >= args.top_k:
                break

        result = {
            "query": {
                "char": classes[query_index],
                "sample_image": sample_paths[query_index],
            },
            "neighbors": neighbors,
        }
        results.append(result)
        print(
            f"{classes[query_index]}: "
            + ", ".join(f"{item['char']} ({item['score']:.4f})" for item in neighbors)
        )

    json_path = artifacts_dir / "random_neighbors_top10.json"
    image_path = artifacts_dir / "random_neighbors_top10.png"
    json_path.write_text(
        json.dumps(
            {
                "checkpoint": str(checkpoint_path),
                "data_root": str(data_root),
                "index_path": str(index_path),
                "num_queries": len(results),
                "top_k": args.top_k,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    draw_grid(results, image_path)
    print(f"saved_json={json_path}")
    print(f"saved_image={image_path}")


if __name__ == "__main__":
    main()
