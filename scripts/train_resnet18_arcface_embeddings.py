from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFilter
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, Sampler
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
IMAGE_EXTENSIONS = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class Sample:
    path: Path
    label: int


class RandomStrokeWidth:
    def __init__(self, p: float = 0.25) -> None:
        self.p = p

    def __call__(self, image: Image.Image) -> Image.Image:
        if random.random() >= self.p:
            return image
        # MinFilter expands black strokes; MaxFilter thins them on white background.
        return image.filter(ImageFilter.MinFilter(3) if random.random() < 0.5 else ImageFilter.MaxFilter(3))


class HanziFolderDataset(Dataset):
    def __init__(self, samples: list[Sample], transform: transforms.Compose) -> None:
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        sample = self.samples[index]
        image = Image.open(sample.path).convert("RGB")
        return self.transform(image), sample.label


class PKBatchSampler(Sampler[list[int]]):
    def __init__(
        self,
        label_to_indices: dict[int, list[int]],
        classes_per_batch: int,
        samples_per_class: int,
        batches_per_epoch: int,
        seed: int,
    ) -> None:
        self.label_to_indices = {label: list(indices) for label, indices in label_to_indices.items()}
        self.labels = sorted(self.label_to_indices)
        self.classes_per_batch = classes_per_batch
        self.samples_per_class = samples_per_class
        self.batches_per_epoch = batches_per_epoch
        self.seed = seed
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def __iter__(self):
        rng = random.Random(self.seed + self.epoch)
        for _ in range(self.batches_per_epoch):
            labels = rng.sample(self.labels, k=min(self.classes_per_batch, len(self.labels)))
            batch: list[int] = []
            for label in labels:
                indices = self.label_to_indices[label]
                if len(indices) >= self.samples_per_class:
                    batch.extend(rng.sample(indices, k=self.samples_per_class))
                else:
                    batch.extend(rng.choices(indices, k=self.samples_per_class))
            rng.shuffle(batch)
            yield batch

    def __len__(self) -> int:
        return self.batches_per_epoch


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


class ArcFaceHead(nn.Module):
    def __init__(self, embedding_dim: int, num_classes: int, scale: float = 30.0, margin: float = 0.35) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.empty(num_classes, embedding_dim))
        nn.init.xavier_uniform_(self.weight)
        self.scale = scale
        self.margin = margin

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        cosine = nn.functional.linear(embeddings, nn.functional.normalize(self.weight, dim=1)).clamp(-0.999, 0.999)
        theta = torch.acos(cosine)
        target_logits = torch.cos(theta + self.margin)
        one_hot = torch.zeros_like(cosine)
        one_hot.scatter_(1, labels.view(-1, 1), 1.0)
        logits = cosine * (1.0 - one_hot) + target_logits * one_hot
        return logits * self.scale


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def collect_samples(data_root: Path, val_per_class: int, seed: int) -> tuple[list[Sample], list[Sample], list[str]]:
    rng = random.Random(seed)
    classes = sorted([folder.name for folder in data_root.iterdir() if folder.is_dir()])
    train_samples: list[Sample] = []
    val_samples: list[Sample] = []

    for label, character in enumerate(classes):
        folder = data_root / character
        paths = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS])
        if not paths:
            continue
        rng.shuffle(paths)
        split = min(val_per_class, max(1, len(paths) // 5))
        val_paths = paths[:split]
        train_paths = paths[split:]
        val_samples.extend(Sample(path=path, label=label) for path in val_paths)
        train_samples.extend(Sample(path=path, label=label) for path in train_paths)

    return train_samples, val_samples, classes


def build_train_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomAffine(degrees=10, translate=(0.06, 0.06), scale=(0.92, 1.08), shear=5),
            transforms.RandomApply([transforms.ElasticTransform(alpha=28.0, sigma=5.0)], p=0.25),
            RandomStrokeWidth(p=0.25),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )


def build_eval_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )


def make_label_to_indices(samples: list[Sample]) -> dict[int, list[int]]:
    label_to_indices: dict[int, list[int]] = {}
    for index, sample in enumerate(samples):
        label_to_indices.setdefault(sample.label, []).append(index)
    return label_to_indices


def learning_rate_for_step(
    step: int,
    total_steps: int,
    base_lr: float,
    warmup_steps: int,
    min_lr_ratio: float,
) -> float:
    if warmup_steps > 0 and step < warmup_steps:
        return base_lr * float(step + 1) / float(warmup_steps)
    progress = (step - warmup_steps) / max(total_steps - warmup_steps, 1)
    cosine = 0.5 * (1.0 + math.cos(math.pi * min(max(progress, 0.0), 1.0)))
    return base_lr * (min_lr_ratio + (1.0 - min_lr_ratio) * cosine)


def set_optimizer_lr(optimizer: torch.optim.Optimizer, lr: float) -> None:
    for group in optimizer.param_groups:
        group["lr"] = lr


def accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    return float((logits.argmax(dim=1) == labels).float().mean().item())


@torch.inference_mode()
def evaluate(
    model: nn.Module,
    head: ArcFaceHead,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    max_batches: int = 0,
) -> tuple[float, float]:
    model.eval()
    head.eval()
    total_loss = 0.0
    total_acc = 0.0
    total_seen = 0

    for batch_index, (images, labels) in enumerate(loader):
        if max_batches > 0 and batch_index >= max_batches:
            break
        images = images.to(device)
        labels = labels.to(device)
        embeddings = model(images)
        logits = head(embeddings, labels)
        loss = criterion(logits, labels)
        batch_size = labels.size(0)
        total_loss += float(loss.item()) * batch_size
        total_acc += accuracy(logits, labels) * batch_size
        total_seen += batch_size

    return total_loss / max(total_seen, 1), total_acc / max(total_seen, 1)


def save_checkpoint(
    path: Path,
    model: nn.Module,
    head: ArcFaceHead,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    best_val_acc: float,
    classes: list[str],
    args: argparse.Namespace,
    history: list[dict],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "head_state_dict": head.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "epoch": epoch,
            "best_val_acc": best_val_acc,
            "classes": classes,
            "embedding_dim": args.embedding_dim,
            "image_size": 224,
            "normalize_mean": [0.5, 0.5, 0.5],
            "normalize_std": [0.5, 0.5, 0.5],
            "history": history,
            "args": vars(args),
        },
        path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ResNet18 Hanzi embeddings with ArcFace.")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS_DIR)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--embedding-dim", type=int, choices=[256, 512], default=256)
    parser.add_argument("--classes-per-batch", type=int, default=16)
    parser.add_argument("--samples-per-class", type=int, default=4)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--warmup-epochs", type=float, default=2.0)
    parser.add_argument("--min-lr-ratio", type=float, default=0.05)
    parser.add_argument("--val-per-class", type=int, default=5)
    parser.add_argument("--max-batches-per-epoch", type=int, default=0)
    parser.add_argument("--max-val-batches", type=int, default=0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--visualize-after", action="store_true")
    args = parser.parse_args()

    seed_everything(args.seed)
    data_root = args.data_root.expanduser().resolve()
    artifacts_dir = args.artifacts_dir.expanduser().resolve()
    if not data_root.is_dir():
        raise NotADirectoryError(data_root)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.require_cuda and device.type != "cuda":
        raise RuntimeError("CUDA is required but not available.")

    train_samples, val_samples, classes = collect_samples(data_root, args.val_per_class, args.seed)
    if not train_samples or not val_samples:
        raise RuntimeError("Dataset split is empty.")

    train_dataset = HanziFolderDataset(train_samples, build_train_transform())
    val_dataset = HanziFolderDataset(val_samples, build_eval_transform())
    batch_size = args.classes_per_batch * args.samples_per_class
    batches_per_epoch = math.ceil(len(train_samples) / batch_size)
    if args.max_batches_per_epoch > 0:
        batches_per_epoch = min(batches_per_epoch, args.max_batches_per_epoch)
    sampler = PKBatchSampler(
        label_to_indices=make_label_to_indices(train_samples),
        classes_per_batch=args.classes_per_batch,
        samples_per_class=args.samples_per_class,
        batches_per_epoch=batches_per_epoch,
        seed=args.seed,
    )
    train_loader = DataLoader(
        train_dataset,
        batch_sampler=sampler,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )

    model = ResNet18Embedder(args.embedding_dim).to(device)
    head = ArcFaceHead(args.embedding_dim, len(classes)).to(device)
    optimizer = torch.optim.AdamW(
        list(model.parameters()) + list(head.parameters()),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    criterion = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=args.amp and device.type == "cuda")

    start_epoch = 1
    best_val_acc = 0.0
    history: list[dict] = []
    if args.resume is not None:
        checkpoint = torch.load(args.resume.expanduser().resolve(), map_location=device)
        if checkpoint["classes"] != classes:
            raise RuntimeError("Resume checkpoint classes do not match dataset classes.")
        model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        head.load_state_dict(checkpoint["head_state_dict"], strict=True)
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        start_epoch = int(checkpoint.get("epoch", 0)) + 1
        best_val_acc = float(checkpoint.get("best_val_acc", 0.0))
        history = checkpoint.get("history", [])

    total_steps = args.epochs * len(train_loader)
    warmup_steps = int(args.warmup_epochs * len(train_loader))
    global_step = (start_epoch - 1) * len(train_loader)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "classes.json").write_text(json.dumps(classes, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"data_root={data_root} classes={len(classes)} train={len(train_samples)} val={len(val_samples)} "
        f"batch_size={batch_size} batches_per_epoch={len(train_loader)} device={device} "
        f"gpu={torch.cuda.get_device_name(0) if device.type == 'cuda' else 'none'}"
    )

    for epoch in range(start_epoch, args.epochs + 1):
        sampler.set_epoch(epoch)
        model.train()
        head.train()
        train_loss_sum = 0.0
        train_acc_sum = 0.0
        train_seen = 0

        for images, labels in train_loader:
            lr = learning_rate_for_step(global_step, total_steps, args.lr, warmup_steps, args.min_lr_ratio)
            set_optimizer_lr(optimizer, lr)
            global_step += 1

            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=args.amp and device.type == "cuda"):
                embeddings = model(images)
                logits = head(embeddings, labels)
                loss = criterion(logits, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            batch_size_actual = labels.size(0)
            train_loss_sum += float(loss.item()) * batch_size_actual
            train_acc_sum += accuracy(logits.detach(), labels) * batch_size_actual
            train_seen += batch_size_actual

        train_loss = train_loss_sum / max(train_seen, 1)
        train_acc = train_acc_sum / max(train_seen, 1)
        val_loss, val_acc = evaluate(model, head, val_loader, criterion, device, args.max_val_batches)
        best_val_acc = max(best_val_acc, val_acc)
        epoch_row = {
            "epoch": epoch,
            "lr": lr,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "best_val_acc": best_val_acc,
        }
        history.append(epoch_row)
        print(
            f"epoch={epoch} lr={lr:.6g} train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} best_val_acc={best_val_acc:.4f}"
        )

        save_checkpoint(
            artifacts_dir / "resnet18_arcface_last.pt",
            model,
            head,
            optimizer,
            epoch,
            best_val_acc,
            classes,
            args,
            history,
        )
        if val_acc >= best_val_acc:
            save_checkpoint(
                artifacts_dir / "resnet18_arcface_best.pt",
                model,
                head,
                optimizer,
                epoch,
                best_val_acc,
                classes,
                args,
                history,
            )
        (artifacts_dir / "training_history.json").write_text(
            json.dumps(history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if args.visualize_after:
        visualize_script = Path(__file__).with_name("visualize_resnet18_neighbors.py")
        command = [
            sys.executable,
            str(visualize_script),
            "--data-root",
            str(data_root),
            "--checkpoint",
            str(artifacts_dir / "resnet18_arcface_best.pt"),
            "--artifacts-dir",
            str(artifacts_dir),
            "--rebuild-index",
        ]
        if args.require_cuda:
            command.append("--require-cuda")
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
