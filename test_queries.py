#!/usr/bin/env python3
"""
Скрипт для тестирования на примерах запросов
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.query_processor import QueryProcessor


def test_all_queries():
    """Тестирует все примеры запросов"""
    
    # Список тестовых файлов
    test_files = [
        "query_1_simple.json",
        "query_2_simple.json",
        "query_4_medium.json",
        "query_5_medium.json",
        "query_8_complex.json"
    ]
    
    print("="*70)
    print("ТЕСТИРОВАНИЕ RAG-СИСТЕМЫ")
    print("="*70)
    
    # Инициализация (можно отключить LLM для быстрого теста)
    processor = QueryProcessor(
        use_llm=False  # Измените на True для полного теста с LLM
    )
    
    results = []
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"\n⚠ Файл {test_file} не найден, пропускаем...")
            continue
        
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
        
        # Обработка
        try:
            response = processor.process_query(
                query=query,
                complexity=test_data.get('complexity'),
                query_id=test_data.get('id')
            )
            
            actual_count = response['response']['items_count']
            actual_cost = response['response']['total_cost']
            
            print(f"Найдено товаров: {actual_count}")
            print(f"Общая стоимость: {actual_cost}")
            
            # Сохраняем результат
            output_file = f"result_{Path(test_file).stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Результат сохранен в {output_file}")
            
            results.append({
                'test': test_file,
                'success': True,
                'query': query,
                'found': actual_count
            })
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            results.append({
                'test': test_file,
                'success': False,
                'error': str(e)
            })
    
    # Итоги
    print(f"\n{'='*70}")
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print('='*70)
    
    success_count = sum(1 for r in results if r.get('success'))
    total_count = len(results)
    
    print(f"Успешно: {success_count}/{total_count}")
    
    for result in results:
        status = "✓" if result.get('success') else "✗"
        print(f"{status} {result['test']}")
        if result.get('success'):
            print(f"   Найдено: {result.get('found')} товаров")
        else:
            print(f"   Ошибка: {result.get('error')}")
    
    print('='*70)


if __name__ == "__main__":
    test_all_queries()
