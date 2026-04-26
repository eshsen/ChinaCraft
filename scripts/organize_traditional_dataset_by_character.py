from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "Dataset"
    / "Traditional-Chinese-Handwriting-Dataset-ready"
    / "cleaned_data_50_50"
    / "cleaned_data(50_50)"
)
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "Dataset"
    / "Traditional-Chinese-Handwriting-Dataset-ready"
    / "by_character"
)
IMAGE_EXTENSIONS = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class PlanItem:
    source: str
    target: str
    character: str


def character_from_filename(path: Path) -> str | None:
    stem = path.stem.strip()
    if "_" not in stem:
        return None
    character = stem.split("_", 1)[0].strip()
    return character or None


def unique_target_path(output_root: Path, character: str, source_path: Path) -> Path:
    target_dir = output_root / character
    target = target_dir / source_path.name
    if not target.exists():
        return target

    suffix = source_path.suffix
    stem = source_path.stem
    counter = 1
    while True:
        candidate = target_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def build_plan(source_root: Path, output_root: Path) -> tuple[list[PlanItem], list[str]]:
    plan: list[PlanItem] = []
    skipped: list[str] = []

    for source_path in sorted(source_root.rglob("*")):
        if not source_path.is_file() or source_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        character = character_from_filename(source_path)
        if character is None:
            skipped.append(str(source_path))
            continue

        target_path = unique_target_path(output_root, character, source_path)
        plan.append(
            PlanItem(
                source=str(source_path),
                target=str(target_path),
                character=character,
            )
        )

    return plan, skipped


def apply_plan(plan: list[PlanItem], mode: str) -> None:
    for item in plan:
        source = Path(item.source)
        target = Path(item.target)
        target.parent.mkdir(parents=True, exist_ok=True)

        if mode == "copy":
            shutil.copy2(source, target)
        elif mode == "move":
            shutil.move(str(source), str(target))
        else:
            raise ValueError(f"Unsupported mode: {mode}")


def write_report(report_path: Path, plan: list[PlanItem], skipped: list[str], applied: bool, mode: str) -> None:
    counts: dict[str, int] = {}
    for item in plan:
        counts[item.character] = counts.get(item.character, 0) + 1

    report = {
        "applied": applied,
        "mode": mode,
        "total_images": len(plan),
        "total_characters": len(counts),
        "character_counts": dict(sorted(counts.items())),
        "skipped": skipped,
        "items": [asdict(item) for item in plan],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Put every Traditional Chinese image into its character folder.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=["copy", "move"], default="copy")
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    source_root = args.source.expanduser().resolve()
    output_root = args.output.expanduser().resolve()
    report_path = (args.report or (output_root.parent / "organize_by_character_report.json")).expanduser().resolve()

    if not source_root.is_dir():
        raise NotADirectoryError(source_root)
    if source_root == output_root or output_root in source_root.parents:
        raise RuntimeError("Output folder must not be inside the source folder.")

    plan, skipped = build_plan(source_root, output_root)
    write_report(report_path, plan, skipped, applied=False, mode=args.mode)

    characters = sorted({item.character for item in plan})
    print(f"source={source_root}")
    print(f"output={output_root}")
    print(f"mode={args.mode}")
    print(f"planned_images={len(plan)}")
    print(f"planned_characters={len(characters)}")
    print(f"skipped={len(skipped)}")
    print(f"report={report_path}")
    print(f"first_characters={characters[:20]}")

    if not args.apply:
        print("dry-run only; rerun with --apply to create folders")
        return

    apply_plan(plan, args.mode)
    write_report(report_path, plan, skipped, applied=True, mode=args.mode)
    print("done")


if __name__ == "__main__":
    main()
