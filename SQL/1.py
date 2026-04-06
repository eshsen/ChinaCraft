import json
import sqlite3
import os

def merge_json_files():
    """Объединяет переводы и HSK уровни в один JSON файл"""
    
    print("=" * 60)
    print("🔄 ОБЪЕДИНЕНИЕ JSON ФАЙЛОВ")
    print("=" * 60)
    
    # Загружаем файл с переводами
    print("\n📂 Загрузка hanzi_with_translations.json...")
    with open("hanzi_with_translations.json", "r", encoding="utf-8") as f:
        translations_data = json.load(f)
    print(f"   ✓ Загружено {len(translations_data)} записей с переводами")
    
    # Загружаем файл с HSK уровнями
    print("\n📂 Загрузка hanzi_with_hsk.json...")
    with open("hanzi_with_hsk.json", "r", encoding="utf-8") as f:
        hsk_data = json.load(f)
    print(f"   ✓ Загружено {len(hsk_data)} записей с HSK")
    
    # Создаём словарь для быстрого поиска HSK уровней
    hsk_dict = {}
    for item in hsk_data:
        char = item.get("char")
        hsk_level = item.get("hsk_level")
        if char and hsk_level:
            hsk_dict[char] = hsk_level
    
    print(f"\n📊 Найдено HSK уровней для {len(hsk_dict)} иероглифов")
    
    # Добавляем HSK уровни в файл с переводами
    updated_count = 0
    for item in translations_data:
        char = item.get("char")
        if char in hsk_dict:
            item["hsk_level"] = hsk_dict[char]
            updated_count += 1
    
    # Сохраняем объединённый файл
    output_file = "hanzi_with_translations.json"
    print(f"\n💾 Сохранение объединённого файла...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(translations_data, f, ensure_ascii=False, indent=2)
    
    print(f"   ✓ Добавлено HSK уровней для {updated_count} иероглифов")
    print(f"   ✓ Сохранено в {output_file}")
    
    return translations_data

def create_new_database_from_json(json_file="hanzi_with_translations.json", db_file="hanzi_database.db"):
    """Создаёт новую базу данных из объединённого JSON файла"""
    
    print("\n" + "=" * 60)
    print("🗄️ СОЗДАНИЕ НОВОЙ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    # Загружаем JSON
    print(f"\n📂 Загрузка {json_file}...")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"   ✓ Загружено {len(data)} иероглифов")
    
    # Удаляем старую базу данных, если она существует
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"   ✓ Удалена старая база данных {db_file}")
    
    # Создаём новую базу данных
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
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
        variant TEXT,
        translation_ru TEXT,
        hsk_level INTEGER
    )
    """)
    print("   ✓ Таблица создана")
    
    # Вставляем данные
    inserted = 0
    for entry in data:
        # Обрабатываем pinyin
        pinyin_list = entry.get("pinyin", [])
        if isinstance(pinyin_list, str):
            try:
                pinyin_list = json.loads(pinyin_list)
            except:
                pinyin_list = []
        pinyin_json = json.dumps(pinyin_list, ensure_ascii=False)
        
        # Получаем значения
        try:
            cursor.execute("""
                INSERT INTO hanzi (
                    id, char, strokes, pinyin, radicals,
                    frequency, structure, traditional, variant,
                    translation_ru, hsk_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.get("index") or entry.get("id"),
                entry.get("char"),
                entry.get("strokes"),
                pinyin_json,
                entry.get("radicals"),
                entry.get("frequency"),
                entry.get("structure"),
                entry.get("traditional"),
                entry.get("variant"),
                entry.get("translation_ru"),
                entry.get("hsk_level")
            ))
            inserted += 1
        except Exception as e:
            print(f"   ✗ Ошибка при вставке {entry.get('char')}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"   ✓ Вставлено {inserted} записей")
    print(f"   ✓ База данных сохранена как {db_file}")
    
    return inserted

def verify_new_database(db_file="hanzi_database.db"):
    """Проверяет новую базу данных"""
    
    print("\n" + "=" * 60)
    print("✅ ПРОВЕРКА НОВОЙ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Проверяем структуру таблицы
    cursor.execute("PRAGMA table_info(hanzi)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"\n📋 Колонки в таблице:")
    for col in columns:
        print(f"   - {col}")
    
    # Проверяем количество записей
    cursor.execute("SELECT COUNT(*) FROM hanzi")
    total = cursor.fetchone()[0]
    print(f"\n📚 Всего иероглифов: {total}")
    
    # Проверяем наличие переводов
    cursor.execute("SELECT COUNT(*) FROM hanzi WHERE translation_ru IS NOT NULL AND translation_ru != ''")
    with_translation = cursor.fetchone()[0]
    print(f"🌐 С переводом: {with_translation}")
    
    # Проверяем наличие HSK
    cursor.execute("SELECT COUNT(*) FROM hanzi WHERE hsk_level IS NOT NULL")
    with_hsk = cursor.fetchone()[0]
    print(f"🏷️ С HSK уровнем: {with_hsk}")
    
    # Показываем примеры
    print(f"\n🔍 Примеры иероглифов:")
    cursor.execute("SELECT char, translation_ru, hsk_level FROM hanzi WHERE translation_ru IS NOT NULL AND hsk_level IS NOT NULL LIMIT 5")
    examples = cursor.fetchall()
    for char, translation, hsk in examples:
        print(f"   {char} → {translation} (HSK {hsk})")
    
    conn.close()
    print("\n" + "=" * 60)

def show_statistics(db_file="hanzi_database.db"):
    """Показывает статистику по HSK уровням"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print("\n📊 СТАТИСТИКА ПО HSK УРОВНЯМ:")
    print("-" * 40)
    
    for level in range(1, 7):
        cursor.execute("SELECT COUNT(*) FROM hanzi WHERE hsk_level = ?", (level,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   HSK {level}: {count} иероглифов")
    
    conn.close()

if __name__ == "__main__":
    print("\n" + "🀄️" * 20)
    print("ОБЪЕДИНЕНИЕ И СОЗДАНИЕ БАЗЫ ДАННЫХ")
    print("🀄️" * 20)
    
    # Шаг 1: Объединяем JSON файлы
    merged_data = merge_json_files()
    
    # Шаг 2: Создаём новую базу данных
    create_new_database_from_json("hanzi_with_translations.json", "hanzi_database.db")
    
    # Шаг 3: Проверяем результат
    verify_new_database("hanzi_database.db")
    
    # Шаг 4: Показываем статистику по HSK
    show_statistics("hanzi_database.db")
    
    print("\n" + "=" * 60)
    print("✅ ГОТОВО!")
    print("=" * 60)
    print("\n📁 Теперь у вас есть:")
    print("   1. hanzi_with_translations.json - объединённый JSON (переводы + HSK)")
    print("   2. hanzi_database.db - новая база данных (переводы + HSK)")
    print("\n💡 Старые файлы можно удалить:")
    print("   - hanzi_with_hsk.json (уже не нужен)")
    print("   - старый hanzi_database.db (перезаписан)")
    print("=" * 60)