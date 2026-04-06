import json
import time
from deep_translator import GoogleTranslator

def add_translations_to_json(input_file="hanzi.json", output_file="hanzi_with_translations.json"):
    """Добавляет перевод каждого иероглифа в JSON"""
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Исправлено: используем правильный код языка
    translator = GoogleTranslator(source='zh-CN', target='ru')
    
    total = len(data)
    translated_count = 0
    error_count = 0
    
    for i, item in enumerate(data, 1):
        char = item.get("char")
        if char:
            try:
                translation = translator.translate(char)
                item["translation_ru"] = translation
                print(f"[{i}/{total}] ✓ {char} → {translation}")
                translated_count += 1
            except Exception as e:
                print(f"[{i}/{total}] ✗ Ошибка с {char}: {e}")
                item["translation_ru"] = ""
                error_count += 1
            
            # Пауза, чтобы не заблокировали за слишком много запросов
            time.sleep(0.3)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Готово!")
    print(f"   Переведено: {translated_count}")
    print(f"   Ошибок: {error_count}")
    print(f"   Сохранено в {output_file}")

# Запуск
add_translations_to_json()