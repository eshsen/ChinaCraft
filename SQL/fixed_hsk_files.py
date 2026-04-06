def load_chars_from_file(filename):
    """Загружает иероглифы из файла, убирая пробелы и пустые строки"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            # Извлекаем все китайские иероглифы (диапазон Unicode 4E00-9FFF)
            import re
            chars = re.findall(r'[\u4e00-\u9fff]', content)
            return set(chars)
    except FileNotFoundError:
        print(f"Файл {filename} не найден!")
        return set()

def save_chars_to_file(filename, chars_set):
    """Сохраняет набор иероглифов в файл (по одному в строку)"""
    with open(filename, 'w', encoding='utf-8') as f:
        for char in sorted(chars_set):
            f.write(char + '\n')

def main():
    levels = [1, 2, 3, 4, 5, 6]
    filenames = {level: f"hsk{level}.txt" for level in levels}
    
    # Загружаем все наборы иероглифов
    all_chars = {}
    for level in levels:
        all_chars[level] = load_chars_from_file(filenames[level])
        print(f"Загружено {len(all_chars[level])} иероглифов из hsk{level}.txt")
    
    # Накопленный набор всех иероглифов с предыдущих уровней
    accumulated = set()
    
    # Обрабатываем каждый уровень (начиная с HSK1)
    for level in levels:
        current = all_chars[level]
        
        if level == 1:
            # HSK1 сохраняем как есть (в нём нечего удалять)
            new_chars = current
        else:
            # Удаляем из текущего уровня все иероглифы, уже встречавшиеся ранее
            duplicates = current & accumulated
            new_chars = current - accumulated
            print(f"  HSK{level}: найдено дублей с предыдущими уровнями: {len(duplicates)}")
        
        # Сохраняем очищенный набор
        output_filename = f"hsk{level}_unique.txt"
        save_chars_to_file(output_filename, new_chars)
        print(f"  HSK{level}: сохранено {len(new_chars)} уникальных иероглифов в {output_filename}")
        
        # Добавляем иероглифы текущего уровня в накопленный набор
        accumulated.update(current)
    
    print("\nГотово! Созданы файлы:")
    for level in levels:
        print(f"  - hsk{level}_unique.txt")

if __name__ == "__main__":
    main()