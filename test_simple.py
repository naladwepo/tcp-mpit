#!/usr/bin/env python3
"""
Тестирование на примерах запросов (упрощенная версия)
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_loader import DataLoader
from src.cost_calculator import create_response_json


class SimpleSearchEngine:
    """Простой поисковый движок на основе совпадения слов"""
    
    def __init__(self, products_df):
        self.products = products_df.to_dict('records')
    
    def search(self, query, top_k=10):
        """Простой текстовый поиск"""
        query_words = set(query.lower().split())
        
        # Оцениваем релевантность каждого товара
        scored_products = []
        for product in self.products:
            name = product.get('name', '').lower()
            category = product.get('category', '').lower()
            text = f"{name} {category}"
            
            # Подсчитываем совпадения слов и частичные совпадения
            score = 0
            for word in query_words:
                if word in text:
                    score += 2
                # Частичное совпадение
                elif any(word in text_word for text_word in text.split()):
                    score += 1
            
            if score > 0:
                scored_products.append((product, score))
        
        # Сортируем по релевантности
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        return scored_products[:top_k]


def test_query(search_engine, test_file):
    """Тестирует один запрос"""
    
    print(f"\n{'='*70}")
    print(f"Тест: {test_file}")
    print('='*70)
    
    # Загрузка теста
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    query = test_data.get('query', '')
    expected = test_data.get('response', {})
    
    print(f"Запрос: {query}")
    print(f"Ожидается товаров: {expected.get('items_count', 'N/A')}")
    print(f"Ожидаемая стоимость: {expected.get('total_cost', 'N/A')}")
    
    # Поиск
    try:
        results = search_engine.search(query, top_k=10)
        
        if not results:
            print("\n⚠ Ничего не найдено")
            return False
        
        # Формируем ответ
        found_items = [product for product, score in results]
        response = create_response_json(
            found_items,
            query_id=test_data.get('id'),
            complexity=test_data.get('complexity')
        )
        
        # Выводим результат
        resp = response.get('response', {})
        print(f"\nНайдено товаров: {resp.get('items_count', 0)}")
        print(f"Общая стоимость: {resp.get('total_cost', '0 руб.')}")
        
        # Сохраняем результат
        output_file = f"result_{Path(test_file).stem}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Результат сохранен в {output_file}")
        
        # Показываем первые результаты
        items = resp.get('found_items', [])
        if items:
            print(f"\nПервые 3 результата:")
            for i, item in enumerate(items[:3], 1):
                name = item.get('name', '')
                if len(name) > 60:
                    name = name[:57] + "..."
                print(f"  {i}. {name}")
                print(f"     {item.get('cost', '0 руб.')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция"""
    
    print("="*70)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ (упрощенная версия)")
    print("="*70)
    
    # Загрузка данных
    print("\nЗагрузка данных...")
    try:
        loader = DataLoader()
        df = loader.combine_datasets()
        print(f"✓ Загружено {len(df)} товаров")
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        return
    
    # Создание поискового движка
    print("Инициализация поиска...")
    search_engine = SimpleSearchEngine(df)
    print("✓ Поисковый движок готов")
    
    # Список тестовых файлов
    test_files = [
        "query_1_simple.json",
        "query_2_simple.json",
        "query_4_medium.json",
        "query_5_medium.json",
        "query_8_complex.json"
    ]
    
    results = []
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"\n⚠ Файл {test_file} не найден, пропускаем...")
            continue
        
        success = test_query(search_engine, test_file)
        results.append((test_file, success))
    
    # Итоги
    print(f"\n{'='*70}")
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print('='*70)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"Успешно: {success_count}/{total_count}")
    
    for test_file, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {test_file}")
    
    print('='*70)
    print("\nПримечание: Используется упрощенный текстовый поиск.")
    print("Для более точных результатов используйте векторный поиск:")
    print("  python main.py --no-llm --test query_1_simple.json")
    print('='*70)


if __name__ == "__main__":
    main()
