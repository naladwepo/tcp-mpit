#!/usr/bin/env python3
"""
Демонстрационный скрипт - использует простой поиск
(векторный поиск отключен из-за проблем совместимости)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_loader import DataLoader
from src.cost_calculator import create_response_json
import json


class SimpleSearchEngine:
    """Простой поисковый движок на основе совпадения слов"""
    
    def __init__(self, products_df):
        self.products = products_df.to_dict('records')
    
    def search(self, query, top_k=5):
        """Простой текстовый поиск"""
        query_words = set(query.lower().split())
        
        # Оцениваем релевантность каждого товара
        scored_products = []
        for product in self.products:
            name = product.get('name', '').lower()
            category = product.get('category', '').lower()
            text = f"{name} {category}"
            
            # Подсчитываем совпадения слов
            score = sum(1 for word in query_words if word in text)
            
            if score > 0:
                scored_products.append((product, score))
        
        # Сортируем по релевантности
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        return scored_products[:top_k]


def demo():
    """Демонстрация работы системы"""
    
    print("\n" + "="*70)
    print("ДЕМОНСТРАЦИЯ RAG-СИСТЕМЫ (текстовый поиск)")
    print("="*70)
    print("\nИнициализация системы...\n")
    
    # Загрузка данных
def demo():
    """Демонстрация работы системы"""
    
    print("\n" + "="*70)
    print("ДЕМОНСТРАЦИЯ RAG-СИСТЕМЫ (текстовый поиск)")
    print("="*70)
    print("\nИнициализация системы...\n")
    
    # Загрузка данных
    try:
        print("[1/2] Загрузка данных...")
        loader = DataLoader()
        df = loader.combine_datasets()
        print(f"✓ Загружено {len(df)} товаров")
        
        print("\n[2/2] Инициализация поиска...")
        search_engine = SimpleSearchEngine(df)
        print("✓ Поисковый движок готов\n")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Демонстрационные запросы
    demo_queries = [
        ("Гайка М6", "Простой поиск по названию"),
        ("Короб 200x200", "Поиск с размерами"),
        ("Лоток перфорированный", "Поиск по категории"),
        ("Крышка горячее цинкование", "Поиск с характеристиками"),
    ]
    
    print("="*70)
    print("ДЕМОНСТРАЦИОННЫЕ ЗАПРОСЫ")
    print("="*70)
    
    for query, description in demo_queries:
        print(f"\n{'='*70}")
        print(f"📝 Запрос: {query}")
        print(f"   ({description})")
        print('='*70)
        
        try:
            # Простой текстовый поиск
            results = search_engine.search(query, top_k=5)
            found_items = [product for product, score in results]
            response = create_response_json(found_items)
            
            # Красивый вывод
            resp = response.get('response', {})
            items = resp.get('found_items', [])
            
            print(f"\n✓ Найдено: {resp.get('items_count', 0)} товаров")
            print(f"💰 Общая стоимость: {resp.get('total_cost', '0 руб.')}")
            
            if items:
                print(f"\nПервые 3 результата:")
                for i, item in enumerate(items[:3], 1):
                    name = item.get('name', '')
                    if len(name) > 60:
                        name = name[:57] + "..."
                    print(f"  {i}. {name}")
                    print(f"     {item.get('cost', '0 руб.')}")
            
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*70)
    print("\n⚠ Используется простой текстовый поиск")
    print("Для векторного поиска с ML-моделями потребуется:")
    print("  - Исправить проблемы с torch/sentence-transformers")
    print("  - Или использовать другое окружение")
    print("\nАльтернатива: используйте demo_simple.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    demo()
