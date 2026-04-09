"""
Редактор переводов иероглифов HSK 1 прямо в терминале.
Показывает иероглиф с текущим переводом — можно принять или ввести новый.

Управление:
  Enter         — оставить текущий перевод, перейти к следующему
  новый текст   — заменить перевод и перейти дальше
  b             — вернуться к предыдущему
  save          — сохранить изменения в файл
  q             — сохранить и выйти
  q!            — выйти без сохранения
"""

import json
import os
import sys
import shutil

FILE = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), "hanzi_with_translations.json")


def load_data(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(path: str, all_data: list[dict]):
    backup = path + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
        print(f"  Бэкап создан: {backup}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)


def show_card(item: dict, pos: int, total: int, changed: int):
    os.system("clear" if os.name != "nt" else "cls")
    pinyin = ", ".join(item.get("pinyin", []))
    trans = item.get("translation_ru", "") or ""

    print("=" * 55)
    print(f"  Редактор HSK 1  |  {pos + 1}/{total}  |  Изменено: {changed}")
    print("=" * 55)
    print()
    print(f"      иероглиф :  {item['char']}")
    print(f"       пиньинь :  {pinyin}")
    print(f"       радикал :  {item.get('radicals', '')}")
    print(f"         черты :  {item.get('strokes', '')}")
    print()
    print(f"  ▸ перевод    :  {trans}")
    print()
    print("-" * 55)
    print("  Enter=ок  новый текст=заменить  b=назад")
    print("  save=сохранить  q=сохранить+выйти  q!=выйти без сохранения")


def main():
    all_data = load_data(FILE)

    # индексы HSK1 в общем списке
    hsk1_indices = [i for i, d in enumerate(
        all_data) if d.get("hsk_level") == 1]
    total = len(hsk1_indices)

    if total == 0:
        print("Иероглифов HSK 1 не найдено.")
        return

    pos = 0
    changed = 0
    edits: dict[int, str] = {}  # global_index -> new translation

    while True:
        gi = hsk1_indices[pos]
        item = all_data[gi]

        # показать текущее (с учётом несохранённых правок)
        if gi in edits:
            item = {**item, "translation_ru": edits[gi]}

        show_card(item, pos, total, changed)

        try:
            cmd = input("\n  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if cmd == "q":
            if edits:
                for idx, val in edits.items():
                    all_data[idx]["translation_ru"] = val
                save_data(FILE, all_data)
                print(f"\n  Сохранено {changed} изменений.")
            print("  Выход.")
            break

        elif cmd == "q!":
            print("  Выход без сохранения.")
            break

        elif cmd == "save":
            if edits:
                for idx, val in edits.items():
                    all_data[idx]["translation_ru"] = val
                save_data(FILE, all_data)
                print(f"\n  Сохранено {changed} изменений.")
                edits.clear()
                input("  Enter чтобы продолжить...")
            else:
                print("\n  Нечего сохранять.")
                input("  Enter чтобы продолжить...")

        elif cmd == "b":
            pos = max(0, pos - 1)

        elif cmd == "":
            # принять и дальше
            pos = min(pos + 1, total - 1)

        else:
            # новый перевод
            edits[gi] = cmd
            changed += 1
            pos = min(pos + 1, total - 1)


if __name__ == "__main__":
    main()
