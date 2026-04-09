"""
Скрипт для проверки переводов иероглифов.
Показывает иероглиф, пиньинь и перевод постранично.

Управление:
  Enter       — следующая страница
  b           — предыдущая страница
  q           — выход
  число       — перейти к странице
  hsk 1-6     — фильтр по уровню HSK (0 = без уровня)
  hsk all     — сбросить фильтр
  find слово  — поиск по переводу или пиньинь
  empty       — показать только иероглифы без перевода
"""

import json
import sys
import os

FILE = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), "hanzi_with_translations.json")
PAGE_SIZE = 20


def load_data(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_row(item: dict) -> str:
    pinyin = ", ".join(item.get("pinyin", []))
    trans = item.get("translation_ru", "—") or "—"
    hsk = item.get("hsk_level", 0)
    hsk_str = f"HSK{hsk}" if hsk else "    "
    return f"  {item['index']:>5}  {item['char']}  {pinyin:<12} {hsk_str}  {trans}"


def show_page(data: list[dict], page: int, total_pages: int, label: str = ""):
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(data))

    os.system("clear" if os.name != "nt" else "cls")

    header = f"  Проверка переводов иероглифов  |  Всего: {len(data)}"
    if label:
        header += f"  |  {label}"
    print("=" * 70)
    print(header)
    print(f"  Страница {page + 1}/{total_pages}")
    print("=" * 70)
    print(f"  {'№':>5}  字  {'Пиньинь':<12} {'HSK':4}  Перевод")
    print("-" * 70)

    for item in data[start:end]:
        print(format_row(item))

    print("-" * 70)
    print("  Enter=далее  b=назад  q=выход  число=страница")
    print("  hsk N=фильтр  hsk all=сброс  find СЛОВО=поиск  empty=без перевода")


def main():
    all_data = load_data(FILE)
    data = all_data
    label = ""
    page = 0

    while True:
        total_pages = max(1, (len(data) + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(0, min(page, total_pages - 1))

        show_page(data, page, total_pages, label)

        try:
            cmd = input("\n  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if cmd == "q":
            break
        elif cmd == "" or cmd == "n":
            page += 1
        elif cmd == "b":
            page -= 1
        elif cmd.isdigit():
            page = int(cmd) - 1
        elif cmd.startswith("hsk "):
            arg = cmd[4:].strip()
            if arg == "all":
                data = all_data
                label = ""
                page = 0
            elif arg.isdigit():
                level = int(arg)
                data = [d for d in all_data if d.get("hsk_level", 0) == level]
                label = f"HSK {level}" if level else "Без HSK"
                page = 0
        elif cmd.startswith("find "):
            query = cmd[5:].strip()
            if query:
                data = [
                    d for d in all_data
                    if query in (d.get("translation_ru", "") or "").lower()
                    or query in " ".join(d.get("pinyin", [])).lower()
                    or query in d.get("char", "")
                ]
                label = f"Поиск: «{query}» ({len(data)} рез.)"
                page = 0
        elif cmd == "empty":
            data = [
                d for d in all_data
                if not d.get("translation_ru") or d["translation_ru"].strip() == ""
            ]
            label = f"Без перевода ({len(data)} шт.)"
            page = 0

    print("Готово.")


if __name__ == "__main__":
    main()
