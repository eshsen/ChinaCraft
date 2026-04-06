import json
import sqlite3
import os

def create_table_if_not_exists(db_file="hanzi_database.db", json_file="hanzi_with_translations.json"):
    """Создаёт таблицу hanzi из JSON файла, если она не существует"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Проверяем, существует ли таблица
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hanzi'")
    if cursor.fetchone():
        print("✓ Таблица 'hanzi' уже существует")
        conn.close()
        return True
    
    print("📂 Таблица не найдена. Создаём из JSON...")
    
    # Пробуем разные варианты JSON файлов
    possible_json_files = [json_file, "hanzi.json", "hanzi_with_translations.json", "hanzi_complete.json"]
    
    data = None
    for file in possible_json_files:
        if os.path.exists(file):
            print(f"   Загрузка из {file}...")
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            break
    
    if not data:
        print("❌ Не найден ни один JSON файл с иероглифами!")
        conn.close()
        return False
    
    # Создаём таблицу
    cursor.execute("""
    CREATE TABLE hanzi (
        id INTEGER PRIMARY KEY,
        char TEXT NOT NULL,
        strokes INTEGER,
        pinyin TEXT,
        radicals TEXT,
        frequency INTEGER,
        structure TEXT,
        traditional TEXT,
        variant TEXT
    )
    """)
    
    # Вставляем данные
    inserted = 0
    for entry in data:
        # Получаем pinyin как JSON строку
        pinyin_list = entry.get("pinyin", [])
        if isinstance(pinyin_list, str):
            try:
                pinyin_list = json.loads(pinyin_list)
            except:
                pinyin_list = []
        pinyin_json = json.dumps(pinyin_list, ensure_ascii=False)
        
        try:
            cursor.execute("""
                INSERT INTO hanzi (
                    id, char, strokes, pinyin, radicals,
                    frequency, structure, traditional, variant
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.get("index") or entry.get("id"),
                entry.get("char"),
                entry.get("strokes"),
                pinyin_json,
                entry.get("radicals"),
                entry.get("frequency"),
                entry.get("structure"),
                entry.get("traditional"),
                entry.get("variant")
            ))
            inserted += 1
        except Exception as e:
            print(f"   Ошибка вставки: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Таблица создана! Загружено {inserted} иероглифов")
    return True

def add_hsk_column_to_db(db_file="hanzi_database.db"):
    """Добавляет колонку hsk_level в таблицу, если её нет"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Проверяем существование таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hanzi'")
    if not cursor.fetchone():
        print("❌ Таблица 'hanzi' не найдена!")
        conn.close()
        return False
    
    # Проверяем существование колонки
    cursor.execute("PRAGMA table_info(hanzi)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "hsk_level" not in columns:
        cursor.execute("ALTER TABLE hanzi ADD COLUMN hsk_level INTEGER")
        print("✓ Добавлена колонка 'hsk_level'")
    else:
        print("✓ Колонка 'hsk_level' уже существует")
    
    conn.commit()
    conn.close()
    return True

def load_hsk_chars_from_txt(txt_file):
    """Загружает иероглифы из txt файла"""
    
    chars = []
    
    if not os.path.exists(txt_file):
        print(f"❌ Файл {txt_file} не найден!")
        return chars
    
    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Берём первый символ (иероглиф)
                char = line[0] if line else ""
                if char and '\u4e00' <= char <= '\u9fff':
                    chars.append(char)
    
    # Убираем дубликаты
    seen = set()
    unique_chars = []
    for char in chars:
        if char not in seen:
            seen.add(char)
            unique_chars.append(char)
    
    print(f"✓ Загружено {len(unique_chars)} иероглифов из {txt_file}")
    return unique_chars

def update_hsk_level_from_file(txt_file, hsk_level, db_file="hanzi_database.db"):
    """Обновляет hsk_level для иероглифов из txt файла"""
    
    print(f"\n📂 Обработка HSK {hsk_level} из {txt_file}...")
    hsk_chars = load_hsk_chars_from_txt(txt_file)
    
    if not hsk_chars:
        return 0, []
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    updated = 0
    not_found = []
    
    for char in hsk_chars:
        cursor.execute("UPDATE hanzi SET hsk_level = ? WHERE char = ?", (hsk_level, char))
        if cursor.rowcount > 0:
            updated += 1
            print(f"  ✓ {char} → HSK {hsk_level}")
        else:
            not_found.append(char)
            print(f"  ✗ {char} → не найден в БД")
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ Обновлено: {updated}, ❌ Не найдено: {len(not_found)}")
    return updated, not_found

def update_json_with_hsk(json_file="hanzi_with_translations.json", output_json="hanzi_with_hsk.json", db_file="hanzi_database.db"):
    """Обновляет JSON файл, добавляя hsk_level"""
    
    if not os.path.exists(json_file):
        print(f"\n⚠️ {json_file} не найден, ищем другой JSON...")
        for file in ["hanzi.json", "hanzi_complete.json"]:
            if os.path.exists(file):
                json_file = file
                break
        else:
            print("❌ JSON файл не найден!")
            return None
    
    print(f"\n📝 Обновление JSON файла ({json_file})...")
    
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT char, hsk_level FROM hanzi WHERE hsk_level IS NOT NULL")
    hsk_dict = {char: level for char, level in cursor.fetchall()}
    conn.close()
    
    updated = 0
    for item in data:
        char = item.get("char")
        if char in hsk_dict:
            item["hsk_level"] = hsk_dict[char]
            updated += 1
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Обновлено {updated} записей, сохранено в {output_json}")
    return output_json

def show_hsk_statistics(db_file="hanzi_database.db"):
    """Показывает статистику по HSK уровням"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("📊 СТАТИСТИКА HSK УРОВНЕЙ")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM hanzi")
    total = cursor.fetchone()[0]
    print(f"📚 Всего иероглифов в базе: {total}")
    
    cursor.execute("SELECT COUNT(*) FROM hanzi WHERE hsk_level IS NOT NULL")
    with_hsk = cursor.fetchone()[0]
    print(f"🏷️ С HSK меткой: {with_hsk}")
    print(f"❓ Без HSK: {total - with_hsk}")
    
    print("\n📈 Распределение по уровням:")
    for level in range(1, 7):
        cursor.execute("SELECT COUNT(*) FROM hanzi WHERE hsk_level = ?", (level,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   HSK {level}: {count} иероглифов")
    
    print("\n🔍 Примеры иероглифов по уровням:")
    for level in range(1, 7):
        cursor.execute("SELECT char FROM hanzi WHERE hsk_level = ? LIMIT 5", (level,))
        chars = cursor.fetchall()
        if chars:
            examples = ", ".join([c[0] for c in chars])
            print(f"   HSK {level}: {examples}")
    
    conn.close()
    print("=" * 60)

def export_full_json(db_file="hanzi_database.db", output_file="hanzi_complete.json"):
    """Экспортирует всю базу в JSON"""
    
    print(f"\n💾 Экспорт базы в JSON...")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT id, char, strokes, pinyin, radicals, frequency, structure, traditional, variant, hsk_level FROM hanzi")
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        entry = {
            "index": row[0],
            "char": row[1],
            "strokes": row[2],
            "radicals": row[4],
            "frequency": row[5],
            "structure": row[6],
            "hsk_level": row[9]
        }
        try:
            entry["pinyin"] = json.loads(row[3]) if row[3] else []
        except:
            entry["pinyin"] = []
        if row[7]:
            entry["traditional"] = row[7]
        if row[8]:
            entry["variant"] = row[8]
        data.append(entry)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    conn.close()
    print(f"✓ Экспортировано {len(data)} иероглифов в {output_file}")

def verify_search_by_char(db_file="hanzi_database.db"):
    """Проверяет поиск по иероглифу"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("🔍 ПРОВЕРКА ПОИСКА ПО ИЕРОГЛИФУ")
    print("=" * 60)
    
    test_chars = ["一", "二", "三", "人", "口"]
    for char in test_chars:
        cursor.execute("SELECT char, hsk_level FROM hanzi WHERE char = ?", (char,))
        result = cursor.fetchone()
        if result:
            level = result[1] if result[1] else "нет"
            print(f"   ✓ '{result[0]}' → HSK {level}")
        else:
            print(f"   ✗ '{char}' не найден")
    
    conn.close()
    print("=" * 60)

if __name__ == "__main__":
    print("=" * 60)
    print("🀄️ ДОБАВЛЕНИЕ HSK УРОВНЕЙ")
    print("=" * 60)
    
    # ШАГ 1: Создаём таблицу, если её нет
    if not create_table_if_not_exists():
        print("❌ Не удалось создать таблицу. Проверьте наличие JSON файла.")
        exit(1)
    
    # ШАГ 2: Добавляем колонку HSK
    if not add_hsk_column_to_db():
        print("❌ Не удалось добавить колонку HSK.")
        exit(1)
    
    # ШАГ 3: Обновляем уровни из файлов
    hsk_files = {
        1: "hsk1_unique.txt",
        2: "hsk2_unique.txt",
        3: "hsk3_unique.txt",
        4: "hsk4_unique.txt",
        5: "hsk5_unique.txt",
        6: "hsk6_unique.txt"
    }
    
    all_not_found = []
    for level, filename in hsk_files.items():
        if os.path.exists(filename):
            updated, not_found = update_hsk_level_from_file(filename, level)
            all_not_found.extend(not_found)
        else:
            print(f"\n⚠️ {filename} не найден (HSK {level} пропущен)")
    
    # ШАГ 4: Обновляем JSON
    update_json_with_hsk()
    
    # ШАГ 5: Экспортируем полный JSON
    export_full_json()
    
    # ШАГ 6: Показываем статистику
    show_hsk_statistics()
    
    # ШАГ 7: Проверяем поиск
    verify_search_by_char()
    
    # ШАГ 8: Сохраняем ненайденные
    if all_not_found:
        with open("not_found_in_db.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(all_not_found))
        print(f"\n⚠️ {len(all_not_found)} иероглифов не найдено в БД")
        print(f"   Список сохранён в 'not_found_in_db.txt'")
    
    print("\n✅ ГОТОВО!")
    print("\n📁 Созданные файлы:")
    print("   1. hanzi_database.db - обновлённая база данных")
    print("   2. hanzi_with_hsk.json - JSON с HSK уровнями")
    print("   3. hanzi_complete.json - полный экспорт")