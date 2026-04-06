import sqlite3
import json
import random

def test_random_chars(db_file="hanzi_database.db", num_chars=10):
    """Выводит случайные иероглифы из базы данных"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Проверяем, сколько всего иероглифов
    cursor.execute("SELECT COUNT(*) FROM hanzi")
    total = cursor.fetchone()[0]
    print(f"📚 Всего иероглифов в базе: {total}\n")
    print("=" * 70)
    print(f"🎲 {num_chars} СЛУЧАЙНЫХ ИЕРОГЛИФОВ:")
    print("=" * 70)
    
    # Получаем случайные иероглифы (добавили translation_ru)
    cursor.execute(f"SELECT id, char, strokes, pinyin, radicals, frequency, structure, hsk_level, translation_ru FROM hanzi ORDER BY RANDOM() LIMIT {num_chars}")
    
    for i, row in enumerate(cursor.fetchall(), 1):
        id_num, char, strokes, pinyin_json, radicals, frequency, structure, hsk_level, translation = row
        
        # Декодируем pinyin
        try:
            pinyin_list = json.loads(pinyin_json) if pinyin_json else []
            pinyin_str = ", ".join(pinyin_list)
        except:
            pinyin_str = "?"
        
        print(f"\n{i}. Иероглиф: {char}")
        print(f"   ID: {id_num}")
        print(f"   Перевод: {translation if translation else 'нет перевода'}")
        print(f"   Штрихов: {strokes}")
        print(f"   Пиньинь: {pinyin_str}")
        print(f"   Радикал: {radicals}")
        print(f"   Частота: {frequency}")
        print(f"   Структура: {structure}")
        print(f"   HSK уровень: {hsk_level if hsk_level else 'не указан'}")
    
    conn.close()
    print("\n" + "=" * 70)

def test_specific_chars(db_file="hanzi_database.db"):
    """Проверяет конкретные иероглифы"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print("\n🔍 ПРОВЕРКА КОНКРЕТНЫХ ИЕРОГЛИФОВ:")
    print("=" * 70)
    
    test_chars = ["一", "人", "口", "山", "水", "火"]
    
    for char in test_chars:
        cursor.execute("SELECT char, strokes, hsk_level, translation_ru FROM hanzi WHERE char = ?", (char,))
        result = cursor.fetchone()
        if result:
            char_found, strokes, hsk_level, translation = result
            print(f"   ✓ {char_found} → штрихов: {strokes}, HSK: {hsk_level if hsk_level else 'нет'}, перевод: {translation if translation else 'нет'}")
        else:
            print(f"   ✗ {char} не найден")
    
    conn.close()
    print("=" * 70)

def search_char(char, db_file="hanzi_database.db"):
    """Поиск конкретного иероглифа по запросу"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print(f"\n🔍 ПОИСК ИЕРОГЛИФА '{char}':")
    print("=" * 70)
    
    cursor.execute("SELECT char, strokes, pinyin, radicals, frequency, structure, hsk_level, translation_ru FROM hanzi WHERE char = ?", (char,))
    result = cursor.fetchone()
    
    if result:
        char_found, strokes, pinyin_json, radicals, frequency, structure, hsk_level, translation = result
        
        try:
            pinyin_list = json.loads(pinyin_json) if pinyin_json else []
            pinyin_str = ", ".join(pinyin_list)
        except:
            pinyin_str = "?"
        
        print(f"   Иероглиф: {char_found}")
        print(f"   Перевод: {translation if translation else 'нет перевода'}")
        print(f"   Штрихов: {strokes}")
        print(f"   Пиньинь: {pinyin_str}")
        print(f"   Радикал: {radicals}")
        print(f"   Частота: {frequency}")
        print(f"   Структура: {structure}")
        print(f"   HSK уровень: {hsk_level if hsk_level else 'не указан'}")
    else:
        print(f"   ✗ Иероглиф '{char}' не найден")
    
    conn.close()
    print("=" * 70)

if __name__ == "__main__":
    # Проверяем случайные иероглифы
    test_random_chars("hanzi_database.db", 10)
    
    # Проверяем конкретные
    test_specific_chars("hanzi_database.db")
    
    # Можно поискать конкретный иероглиф
    # search_char("爱")