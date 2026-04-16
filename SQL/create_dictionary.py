import json
import shutil
import os
from typing import List, Dict, Any

# ========== КОНФИГУРАЦИЯ ==========
INPUT_FILE = "SQL/hanzi_with_translations.json.bak"
OUTPUT_FILE = "hanzi_with_translations.json"

# Допустимые значения для валидации
VALID_HSK_LEVELS = {1, 2, 3, 4, 5, 6}
VALID_STRUCTURE_TYPES = {"S", "H0", "H1", "H2", "H3", "V0",
                         "V1", "V2", "V3", "B1", "B2", "B3", "B4", "上中下", "左中右", "半包围"}

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ==========


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """Загружает данные из JSON файла"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(file_path: str, data: List[Dict[str, Any]]):
    """Сохраняет данные в JSON файл с красивым форматированием"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводит запись к стандартному формату:
    {"index": int, "char": str, "strokes": int, "pinyin": list,
     "radicals": str, "frequency": int, "structure": str,
     "translation_ru": str, "hsk_level": int}
    """
    # Преобразуем translation_ru: если массив, берём первый элемент или объединяем
    trans = entry.get("translation_ru", "")
    if isinstance(trans, list):
        trans = ", ".join(trans) if trans else ""

    # Преобразуем pinyin: если строка, оборачиваем в список
    pinyin = entry.get("pinyin", [])
    if isinstance(pinyin, str):
        pinyin = [pinyin]

    # Обрабатываем частоту: если None, 0 или пусто, ставим 5 (редкий)
    freq = entry.get("frequency")
    if freq is None or freq == "" or freq == 0:
        freq = 5

    # Обрабатываем структуру: если пусто, ставим "S" (одиночный)
    structure = entry.get("structure", "")
    if not structure:
        structure = "S"

    # Обрабатываем количество черт: если нет или 0, ставим None
    strokes = entry.get("strokes")
    if not strokes or strokes <= 0:
        strokes = None

    return {
        "index": 0,  # временно, потом пересчитаем
        "char": entry.get("char", ""),
        "strokes": strokes,
        "pinyin": pinyin,
        "radicals": entry.get("radicals", ""),
        "frequency": freq,
        "structure": structure,
        "translation_ru": trans,
        "hsk_level": entry.get("hsk_level", 0)
    }


def filter_by_hsk_level(data: List[Dict[str, Any]], level: int) -> List[Dict[str, Any]]:
    """Возвращает список записей с указанным уровнем HSK"""
    return [item for item in data if item.get("hsk_level") == level]


def add_comment_separators(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Добавляет комментарии-разделители между уровнями HSK
    Возвращает список, где между уровнями вставлены строки-комментарии
    """
    result = []
    # Группируем по уровню HSK
    levels = sorted(set(item["hsk_level"]
                    for item in data if item["hsk_level"] > 0))

    for level in levels:
        # Добавляем комментарий перед уровнем
        result.append(f"// === УРОВЕНЬ HSK {level} ===")
        # Добавляем все иероглифы этого уровня
        level_items = [item for item in data if item["hsk_level"] == level]
        result.extend(level_items)

    # Добавляем иероглифы без уровня HSK (если есть)
    no_level = [item for item in data if not item.get(
        "hsk_level") or item["hsk_level"] == 0]
    if no_level:
        result.append("// === ИЕРОГЛИФЫ БЕЗ УРОВНЯ HSK ===")
        result.extend(no_level)

    return result


def reindex_data(data_with_comments: List[Any]) -> List[Any]:
    """
    Перенумеровывает индексы с 1 до конца.
    Комментарии (строки) пропускает.
    """
    current_index = 1
    for i, item in enumerate(data_with_comments):
        if isinstance(item, dict):
            item["index"] = current_index
            current_index += 1
    return data_with_comments

# ========== ФУНКЦИИ ДЛЯ ИНТЕРАКТИВНОГО РЕДАКТИРОВАНИЯ ==========


def edit_entry(entry: Dict[str, Any], level: int) -> Dict[str, Any]:
    """
    Позволяет пользователю отредактировать информацию об иероглифе.
    Возвращает обновлённую запись.
    """
    print("\n" + "="*60)
    print(f"Редактирование иероглифа: {entry['char']} (HSK {level})")
    print("="*60)

    # Показываем текущие значения
    print(f"\nТекущая информация:")
    print(f"  1. Иероглиф (char): {entry['char']}")
    print(f"  2. Черты (strokes): {entry['strokes']}")
    print(f"  3. Пиньинь (pinyin): {entry['pinyin']}")
    print(f"  4. Ключ (radicals): {entry['radicals']}")
    print(f"  5. Частота (frequency): {entry['frequency']}")
    print(f"  6. Структура (structure): {entry['structure']}")
    print(f"  7. Перевод (translation_ru): {entry['translation_ru']}")
    print(f"  8. Уровень HSK (hsk_level): {entry['hsk_level']}")
    print(f"  0. Пропустить, ничего не менять")

    choice = input("\nЧто хотите изменить? (0-8): ").strip()

    if choice == "0":
        return entry

    field_map = {
        "1": "char",
        "2": "strokes",
        "3": "pinyin",
        "4": "radicals",
        "5": "frequency",
        "6": "structure",
        "7": "translation_ru",
        "8": "hsk_level"
    }

    if choice in field_map:
        field = field_map[choice]
        current = entry[field]

        if field == "pinyin":
            new_value = input(
                f"Введите пиньинь (через запятую, например: zhōng,guó): ").strip()
            if new_value:
                entry[field] = [p.strip() for p in new_value.split(",")]
                print(f"✓ Пиньинь изменён на {entry[field]}")
        elif field == "strokes":
            new_value = input(
                f"Введите количество черт (было {current}): ").strip()
            if new_value:
                entry[field] = int(new_value)
                print(f"✓ Черты изменены на {entry[field]}")
        elif field == "frequency":
            new_value = input(
                f"Введите частоту (1-5, 1=очень часто, 5=редко): ").strip()
            if new_value:
                entry[field] = int(new_value)
                print(f"✓ Частота изменена на {entry[field]}")
        elif field == "hsk_level":
            new_value = input(
                f"Введите уровень HSK (1-6, или 0 если без уровня): ").strip()
            if new_value:
                entry[field] = int(new_value)
                print(f"✓ Уровень HSK изменён на {entry[field]}")
        else:
            new_value = input(
                f"Введите новое значение (было '{current}'): ").strip()
            if new_value:
                if field == "strokes":
                    entry[field] = int(new_value)
                elif field == "frequency":
                    entry[field] = int(new_value)
                elif field == "hsk_level":
                    entry[field] = int(new_value)
                else:
                    entry[field] = new_value
                print(f"✓ {field} изменён на {entry[field]}")

    return entry


def add_new_char(level: int, current_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Добавляет новый иероглиф к указанному уровню
    """
    print("\n" + "="*60)
    print(f"Добавление нового иероглифа на уровень HSK {level}")
    print("="*60)

    new_char = input("Введите иероглиф: ").strip()
    if not new_char:
        print("❌ Иероглиф не может быть пустым!")
        return None

    # Проверяем, нет ли уже такого иероглифа
    for item in current_data:
        if isinstance(item, dict) and item.get("char") == new_char:
            print(f"❌ Иероглиф '{new_char}' уже существует в словаре!")
            return None

    # Собираем информацию
    strokes = input("Количество черт: ").strip()
    strokes = int(strokes) if strokes else None

    pinyin_input = input("Пиньинь (через запятую, например: ni,hao): ").strip()
    pinyin = [p.strip()
              for p in pinyin_input.split(",")] if pinyin_input else []

    radicals = input("Ключ (радикал): ").strip()

    frequency = input("Частота (1-5, 1=очень часто, 5=редко): ").strip()
    frequency = int(frequency) if frequency else 5

    structure = input("Структура (S/H0/H1/.../上中下 и т.д.): ").strip()
    if not structure:
        structure = "S"

    translation = input("Перевод на русский: ").strip()

    new_entry = {
        "index": 0,  # временно
        "char": new_char,
        "strokes": strokes,
        "pinyin": pinyin,
        "radicals": radicals,
        "frequency": frequency,
        "structure": structure,
        "translation_ru": translation,
        "hsk_level": level
    }

    print(f"\n✅ Новый иероглиф '{new_char}' создан!")
    return new_entry


def interactive_edit_for_level(data_with_comments: List[Any], level: int) -> List[Any]:
    """
    Позволяет пользователю пройти по всем иероглифам выбранного уровня,
    отредактировать их, а затем добавить новый иероглиф.
    """
    # Находим все записи (словари) этого уровня
    level_entries = []
    level_indices = []  # позиции в общем списке

    for i, item in enumerate(data_with_comments):
        if isinstance(item, dict) and item.get("hsk_level") == level:
            level_entries.append(item)
            level_indices.append(i)

    if not level_entries:
        print(f"\n⚠️ Нет иероглифов на уровне HSK {level}")
        return data_with_comments

    print(f"\n📚 Найдено {len(level_entries)} иероглифов на уровне HSK {level}")
    print("="*60)

    # Проходим по каждому иероглифу
    for idx, (entry, pos) in enumerate(zip(level_entries, level_indices), 1):
        print(f"\n[{idx}/{len(level_entries)}]")
        edited = edit_entry(entry, level)
        data_with_comments[pos] = edited

    # Спрашиваем, хочет ли пользователь добавить новый иероглиф
    print("\n" + "="*60)
    add_more = input(
        f"Все иероглифы уровня HSK {level} просмотрены. Добавить новый иероглиф на этот уровень? (y/N): ").strip().lower()

    while add_more == "y":
        new_entry = add_new_char(
            level, [item for item in data_with_comments if isinstance(item, dict)])
        if new_entry:
            # Находим позицию комментария для этого уровня или добавляем в конец уровня
            insert_pos = None
            for i, item in enumerate(data_with_comments):
                if isinstance(item, str) and f"=== УРОВЕНЬ HSK {level} ===" in item:
                    # Ищем конец этого уровня
                    j = i + 1
                    while j < len(data_with_comments):
                        if isinstance(data_with_comments[j], dict) and data_with_comments[j].get("hsk_level") == level:
                            j += 1
                        else:
                            break
                    insert_pos = j
                    break

            if insert_pos is not None:
                data_with_comments.insert(insert_pos, new_entry)
                print(
                    f"✅ Иероглиф '{new_entry['char']}' добавлен на уровень HSK {level}")
            else:
                data_with_comments.append(new_entry)

        add_more = input("Добавить ещё один иероглиф? (y/N): ").strip().lower()

    return data_with_comments

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========


def main():
    print("="*60)
    print("ОБРАБОТЧИК СЛОВАРЯ КИТАЙСКИХ ИЕРОГЛИФОВ")
    print("="*60)

    # 1. Проверяем, существует ли исходный файл .bak
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Ошибка: файл {INPUT_FILE} не найден!")
        return

    # 2. Копируем .bak в .json
    print(f"\n📁 Копирование {INPUT_FILE} -> {OUTPUT_FILE}")
    shutil.copy2(INPUT_FILE, OUTPUT_FILE)
    print(f"✅ Файл {OUTPUT_FILE} создан")

    # 3. Загружаем данные
    print(f"\n📖 Загрузка данных из {OUTPUT_FILE}...")
    raw_data = load_data(OUTPUT_FILE)
    print(f"✅ Загружено {len(raw_data)} записей")

    # 4. Нормализуем все записи (приводим к единому формату)
    print("\n🔄 Нормализация записей...")
    normalized_data = [normalize_entry(entry) for entry in raw_data]
    print(f"✅ Нормализовано {len(normalized_data)} записей")

    # 5. Добавляем комментарии-разделители по уровням HSK
    print("\n🏷️ Добавление комментариев-разделителей...")
    data_with_comments = add_comment_separators(normalized_data)

    # 6. Делаем сквозную индексацию с 1
    print("\n🔢 Переиндексация (сквозные индексы с 1)...")
    data_with_comments = reindex_data(data_with_comments)

    # Считаем количество иероглифов (не комментариев)
    char_count = sum(
        1 for item in data_with_comments if isinstance(item, dict))
    print(f"✅ Всего иероглифов: {char_count}")

    # 7. Сохраняем промежуточный результат
    save_data(OUTPUT_FILE, data_with_comments)
    print(f"\n💾 Промежуточный результат сохранён в {OUTPUT_FILE}")

    # 8. Интерактивное редактирование
    print("\n" + "="*60)
    print("ИНТЕРАКТИВНОЕ РЕДАКТИРОВАНИЕ")
    print("="*60)

    while True:
        print("\nДоступные уровни HSK: 1, 2, 3, 4, 5, 6")
        level_str = input(
            "Выберите уровень для редактирования (или 'q' для выхода): ").strip()

        if level_str.lower() == 'q':
            break

        try:
            level = int(level_str)
            if level not in VALID_HSK_LEVELS:
                print(f"❌ Уровень должен быть от 1 до 6")
                continue

            # Редактируем выбранный уровень
            data_with_comments = interactive_edit_for_level(
                data_with_comments, level)

            # После изменений переиндексируем заново
            print("\n🔄 Переиндексация после изменений...")
            data_with_comments = reindex_data(data_with_comments)

            # Сохраняем
            save_data(OUTPUT_FILE, data_with_comments)
            print(f"💾 Изменения сохранены в {OUTPUT_FILE}")

        except ValueError:
            print("❌ Пожалуйста, введите число от 1 до 6 или 'q'")

    print("\n" + "="*60)
    print("✅ РАБОТА ЗАВЕРШЕНА")
    print(f"Итоговый файл: {OUTPUT_FILE}")
    print("="*60)


if __name__ == "__main__":
    main()
