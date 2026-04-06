import json
import sqlite3
import os

def create_database_and_table(cursor):
    """Создаёт таблицу для хранения иероглифов"""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hanzi (
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
    print("✓ Таблица 'hanzi' создана (или уже существует)")

def clear_table(cursor):
    """Очищает таблицу перед вставкой (для тестов)"""
    cursor.execute("DELETE FROM hanzi")
    print("✓ Таблица очищена")

def insert_hanzi_data(cursor, data):
    """Вставляет данные из JSON в таблицу"""
    inserted = 0
    errors = 0
    
    for entry in data:
        try:
            # Извлекаем значения по ключам (если ключа нет - ставим None)
            # Преобразуем список pinyin в JSON-строку
            pinyin_list = entry.get("pinyin", [])
            pinyin_json = json.dumps(pinyin_list, ensure_ascii=False)
            
            cursor.execute("""
                INSERT OR REPLACE INTO hanzi (
                    id, char, strokes, pinyin, radicals,
                    frequency, structure, traditional, variant
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.get("index"),  # JSON поле "index" -> SQL столбец "id"
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
            print(f"✗ Ошибка при вставке записи {entry.get('index', '?')}: {e}")
            errors += 1
    
    return inserted, errors

def verify_data(cursor):
    """Проверяет корректность вставленных данных"""
    
    # 1. Общее количество записей
    cursor.execute("SELECT COUNT(*) FROM hanzi")
    total = cursor.fetchone()[0]
    print(f"\n📊 Всего записей в таблице: {total}")
    
    # 2. Проверка первых 5 иероглифов
    print("\n📝 Первые 5 иероглифов:")
    cursor.execute("SELECT id, char, strokes, radicals, frequency FROM hanzi ORDER BY id LIMIT 5")
    for row in cursor.fetchall():
        print(f"   {row[0]}. '{row[1]}' — штрихов: {row[2]}, радикал: '{row[3]}', частота: {row[4]}")
    
    # 3. Проверка последних 5 иероглифов
    print("\n🔚 Последние 5 иероглифов:")
    cursor.execute("SELECT id, char, strokes, radicals, frequency FROM hanzi ORDER BY id DESC LIMIT 5")
    for row in cursor.fetchall():
        print(f"   {row[0]}. '{row[1]}' — штрихов: {row[2]}, радикал: '{row[3]}', частота: {row[4]}")
    
    # 4. Проверка иероглифа с традиционным написанием
    print("\n📖 Примеры с традиционным написанием:")
    cursor.execute("SELECT id, char, traditional, variant FROM hanzi WHERE traditional IS NOT NULL LIMIT 3")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"   {row[0]}. '{row[1]}' → традиционный: '{row[2]}', вариант: '{row[3]}'")
    else:
        print("   (нет записей с traditional)")
    
    # 5. Проверка иероглифа с множественным произношением
    print("\n🔊 Примеры с несколькими произношениями:")
    cursor.execute("SELECT id, char, pinyin FROM hanzi WHERE pinyin LIKE '%[%' AND pinyin NOT LIKE '[\"%\"]' LIMIT 3")
    for row in cursor.fetchall():
        pinyin_list = json.loads(row[2])
        print(f"   {row[0]}. '{row[1]}' → произношения: {', '.join(pinyin_list)}")
    
    # 6. Статистика по количеству штрихов
    print("\n📈 Статистика по количеству штрихов:")
    cursor.execute("""
        SELECT 
            MIN(strokes) as min_strokes,
            MAX(strokes) as max_strokes,
            AVG(strokes) as avg_strokes
        FROM hanzi WHERE strokes IS NOT NULL
    """)
    stats = cursor.fetchone()
    print(f"   Минимум: {stats[0]}, Максимум: {stats[1]}, Среднее: {stats[2]:.1f}")
    
    # 7. Частота встречаемости (frequency)
    print("\n🏆 Частота использования (0=часто, 5=редко):")
    cursor.execute("""
        SELECT frequency, COUNT(*) as count 
        FROM hanzi 
        GROUP BY frequency 
        ORDER BY frequency
    """)
    for row in cursor.fetchall():
        freq_desc = {0: "очень часто", 1: "часто", 2: "средне", 3: "редко", 4: "очень редко", 5: "экзотично"}
        print(f"   Уровень {row[0]} ({freq_desc.get(row[0], 'неизвестно')}): {row[1]} иероглифов")

def main():
    """Основная функция"""
    
    # Путь к файлу (измените на свой)
    json_file = "hanzi.json"
    
    # Проверяем существование файла
    if not os.path.exists(json_file):
        print(f"✗ Файл {json_file} не найден!")
        print("Пожалуйста, укажите правильный путь к JSON-файлу")
        return
    
    print(f"📂 Загрузка файла: {json_file}")
    
    try:
        # Загружаем JSON
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"✓ Загружено {len(data)} записей")
        
        # Создаём/открываем базу данных
        conn = sqlite3.connect("hanzi_database.db")
        cursor = conn.cursor()
        
        # Создаём таблицу
        create_database_and_table(cursor)
        
        # Очищаем для теста (закомментируйте, если не хотите очищать)
        # clear_table(cursor)
        
        # Вставляем данные
        print("\n💾 Вставка данных...")
        inserted, errors = insert_hanzi_data(cursor, data)
        print(f"✓ Вставлено: {inserted}, ошибок: {errors}")
        
        # Сохраняем изменения
        conn.commit()
        
        # Проверяем результат
        verify_data(cursor)
        
        # Закрываем соединение
        conn.close()
        
        print("\n✅ Готово! База данных сохранена как 'hanzi_database.db'")
        
    except json.JSONDecodeError as e:
        print(f"✗ Ошибка парсинга JSON: {e}")
        print("Проверьте, что файл начинается с '[' и заканчивается ']'")
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")

def run_test_with_sample_data():
    """Создаёт тестовые данные и проверяет работу"""
    
    print("\n🧪 ЗАПУСК ТЕСТОВОГО РЕЖИМА\n")
    
    # Тестовые данные (несколько иероглифов в разном порядке полей)
    test_data = [
        {"index": 1, "char": "一", "strokes": 1, "pinyin": ["yī"], "radicals": "一", "frequency": 0, "structure": "D0"},
        {"char": "乙", "strokes": 1, "pinyin": ["yǐ"], "radicals": "乙", "frequency": 1, "structure": "D0", "index": 2},
        {"index": 3, "char": "二", "strokes": 2, "pinyin": ["èr"], "radicals": "二", "frequency": 0, "structure": "D0"},
        {"index": 5, "char": "丁", "strokes": 2, "pinyin": ["dīng", "zhēng"], "radicals": "一", "frequency": 1, "structure": "D0", "traditional": "釘"},
        {"char": "刀", "index": 18, "strokes": 2, "pinyin": ["dāo"], "radicals": "刀", "frequency": 1, "structure": "D0", "variant": "刂"},
        {"index": 21154, "char": "龘", "strokes": 51, "pinyin": ["dá"], "radicals": "龍", "frequency": 5, "structure": "A0"}
    ]
    
    # Создаём тестовую БД
    conn = sqlite3.connect("test_hanzi.db")
    cursor = conn.cursor()
    
    create_database_and_table(cursor)
    clear_table(cursor)
    
    print("📝 Тестовые данные:")
    for item in test_data:
        print(f"   {item}")
    
    inserted, errors = insert_hanzi_data(cursor, test_data)
    print(f"\n✓ Вставлено: {inserted}, ошибок: {errors}")
    
    conn.commit()
    verify_data(cursor)
    
    conn.close()
    print("\n✅ Тест пройден! База данных 'test_hanzi.db' создана")

if __name__ == "__main__":
    # Попытка загрузить реальный файл
    if os.path.exists("hanzi.json"):
        main()
    else:
        print("⚠️ Файл 'hanzi.json' не найден. Запускаем тестовый режим...")
        run_test_with_sample_data()