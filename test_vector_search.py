#!/usr/bin/env python3
"""
Тест векторного поиска с исправленной конфигурацией
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine
import json


def test_vector_search():
    """Тест векторного поиска"""
    
    print("="*70)
    print("ТЕСТ ВЕКТОРНОГО ПОИСКА")
    print("="*70)
    
    # Загрузка данных
    print("\n[1/3] Загрузка данных...")
    loader = DataLoader()
    df = loader.combine_datasets()
    print(f"✓ Загружено {len(df)} товаров")
    
    # Создание поискового движка с рабочей моделью
    print("\n[2/3] Инициализация векторного поиска...")
    try:
        search_engine = VectorSearchEngine(
            model_name="sentence-transformers/all-MiniLM-L6-v2",  # Рабочая модель!
            index_dir="data/index_test"
        )
        
        # Создание индекса
        search_engine.build_index(df, force_rebuild=True)
        print("✓ Индекс создан!")
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Тестовые запросы
    print("\n[3/3] Тестирование поиска...")
    test_queries = [
        "Гайка М6",
        "Короб 200x200",
        "Крышка лотка"
    ]
    
    for query in test_queries:
        print(f"\n  Запрос: {query}")
        try:
            results = search_engine.search(query, top_k=3)
            print(f"  Найдено: {len(results)} товаров")
            
            for i, (product, score) in enumerate(results, 1):
                name = product['name'][:50] + "..." if len(product['name']) > 50 else product['name']
                print(f"    {i}. {name} (score: {score:.3f})")
                
        except Exception as e:
            print(f"  ✗ Ошибка: {e}")
            return False
    
    print("\n" + "="*70)
    print("✓ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    print("Векторный поиск работает корректно!")
    print("="*70)
    return True


if __name__ == "__main__":
    success = test_vector_search()
    sys.exit(0 if success else 1)
