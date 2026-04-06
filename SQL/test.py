import sqlite3
import random
import json

def test_database(db_file="hanzi_database.db"):
    """Проверяет базу данных и выводит 5 случайных иероглифов"""
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Проверяем, есть ли данные в таблице
        cursor.execute("SELECT COUNT(*) FROM hanzi")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"❌ База данных '{db_file}' пуста!")
            return
        
        print(f"✅ База данных '{db_file}' содержит {count} иероглифов\n")
        print("=" * 60)
        print("🎲 5 СЛУЧАЙНЫХ ИЕРОГЛИФОВ:")
        print("=" * 60)
        
        # Получаем 5 случайных записей
        cursor.execute("SELECT id, char, strokes, pinyin, radicals, frequency, structure, traditional, variant FROM hanzi ORDER BY RANDOM() LIMIT 5")
        
        for i, row in enumerate(cursor.fetchall(), 1):
            id_num, char, strokes, pinyin_json, radicals, frequency, structure, traditional, variant = row
            
            # Преобразуем JSON строку pinyin обратно в список
            try:
                pinyin_list = json.loads(pinyin_json) if pinyin_json else []
                pinyin_str = ", ".join(pinyin_list)
            except:
                pinyin_str = pinyin_json or "нет данных"
            
            print(f"\n📌 Иероглиф #{i}:")
            print(f"   ID: {id_num}")
            print(f"   Иероглиф: {char}")
            print(f"   Количество штрихов: {strokes}")
            print(f"   Произношение: {pinyin_str}")
            print(f"   Радикал: {radicals}")
            print(f"   Частота: {frequency} ({'очень часто' if frequency==0 else 'часто' if frequency==1 else 'средне' if frequency==2 else 'редко' if frequency==3 else 'очень редко' if frequency==4 else 'экзотично'})")
            print(f"   Структура: {structure}")
            
            if traditional:
                print(f"   Традиционное написание: {traditional}")
            if variant:
                print(f"   Вариант: {variant}")
        
        # Дополнительная статистика
        print("\n" + "=" * 60)
        print("📊 БЫСТРАЯ СТАТИСТИКА:")
        print("=" * 60)
        
        # Самый частый и редкий иероглиф по частоте
        cursor.execute("SELECT char, frequency FROM hanzi WHERE frequency = (SELECT MIN(frequency) FROM hanzi) LIMIT 1")
        most_freq = cursor.fetchone()
        if most_freq:
            print(f"   🔥 Самый частый: '{most_freq[0]}' (частота {most_freq[1]})")
        
        cursor.execute("SELECT char, frequency FROM hanzi WHERE frequency = (SELECT MAX(frequency) FROM hanzi) LIMIT 1")
        least_freq = cursor.fetchone()
        if least_freq:
            print(f"   💎 Самый редкий: '{least_freq[0]}' (частота {least_freq[1]})")
        
        # Самый простой и сложный по штрихам
        cursor.execute("SELECT char, strokes FROM hanzi WHERE strokes = (SELECT MIN(strokes) FROM hanzi) LIMIT 1")
        min_strokes = cursor.fetchone()
        if min_strokes:
            print(f"   ✍️  Самый простой: '{min_strokes[0]}' ({min_strokes[1]} штрих(а))")
        
        cursor.execute("SELECT char, strokes FROM hanzi WHERE strokes = (SELECT MAX(strokes) FROM hanzi) LIMIT 1")
        max_strokes = cursor.fetchone()
        if max_strokes:
            print(f"   🐉 Самый сложный: '{max_strokes[0]}' ({max_strokes[1]} штрихов)")
        
        # Количество уникальных радикалов
        cursor.execute("SELECT COUNT(DISTINCT radicals) FROM hanzi WHERE radicals IS NOT NULL")
        unique_radicals = cursor.fetchone()[0]
        print(f"   📚 Уникальных радикалов: {unique_radicals}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка базы данных: {e}")
    except FileNotFoundError:
        print(f"❌ Файл '{db_file}' не найден!")
        print("Сначала запустите main.py для создания базы данных")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

def search_char(char, db_file="hanzi_database.db"):
    """Поиск конкретного иероглифа"""
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, char, strokes, pinyin, radicals, frequency FROM hanzi WHERE char = ?", (char,))
        result = cursor.fetchone()
        
        if result:
            id_num, char, strokes, pinyin_json, radicals, frequency = result
            try:
                pinyin_list = json.loads(pinyin_json)
                pinyin_str = ", ".join(pinyin_list)
            except:
                pinyin_str = pinyin_json
            
            print(f"\n🔍 Найден иероглиф '{char}':")
            print(f"   ID: {id_num}")
            print(f"   Штрихов: {strokes}")
            print(f"   Произношение: {pinyin_str}")
            print(f"   Радикал: {radicals}")
            print(f"   Частота: {frequency}")
        else:
            print(f"\n❌ Иероглиф '{char}' не найден в базе данных")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    # Проверяем основную базу данных
    test_database("hanzi_database.db")
    
    search_char("人")
    search_char("龘")