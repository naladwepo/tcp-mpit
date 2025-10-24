"""
Тест LLM-режима с одним простым запросом
"""

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine
from src.hybrid_processor import HybridQueryProcessor
import time


def test_llm_mode_single_query():
    """
    Тестирует LLM-режим на одном простом запросе
    """
    print("=" * 70)
    print("🚀 ТЕСТ LLM-РЕЖИМА (один запрос)")
    print("=" * 70)
    
    # Загрузка данных
    print("\n📦 Загрузка данных...")
    data_loader = DataLoader()
    products = data_loader.get_products()
    print(f"✓ Загружено {len(products)} товаров")
    
    # Инициализация векторного поиска
    print("\n🔍 Инициализация векторного поиска...")
    search_engine = VectorSearchEngine(
        model_name="intfloat/multilingual-e5-small",
        index_dir="data/index_e5"
    )
    search_engine.build_index(products)
    print("✓ Векторный поиск готов")
    
    # Инициализация с LLM
    print("\n🤖 Инициализация процессора с LLM...")
    start_init = time.time()
    processor = HybridQueryProcessor(
        search_engine=search_engine,
        use_llm=True,  # ✅ LLM-режим
        use_query_enhancement=True,
        use_llm_validator=True,
        use_iterative_search=False
    )
    init_time = time.time() - start_init
    print(f"✓ Процессор готов (инициализация: {init_time:.2f}s)")
    
    # Простой тестовый запрос
    query = "Короб 200x200"
    
    print("\n" + "=" * 70)
    print(f"📋 ЗАПРОС: {query}")
    print("=" * 70)
    
    start_query = time.time()
    result = processor.process_query(
        query=query,
        top_k=3,  # Мало результатов для скорости
        complexity="medium",
        query_id=1,
        use_validation=True
    )
    query_time = time.time() - start_query
    
    print("\n" + "=" * 70)
    print(f"📊 РЕЗУЛЬТАТЫ (время обработки: {query_time:.2f}s)")
    print("=" * 70)
    
    # Результат валидации
    if 'validation' in result and result['validation']:
        validation = result['validation']
        print(f"\n✅ ВАЛИДАЦИЯ:")
        print(f"   Режим: {validation.get('mode', 'unknown')}")
        print(f"   Метод: {validation.get('method', 'N/A')}")
        print(f"   Найдено позиций: {len(validation.get('items', []))}")
        
        if 'items' in validation:
            print("\n   📦 Детализация:")
            for item in validation['items']:
                name = item.get('name', 'N/A')
                quantity = item.get('quantity', 0)
                unit_price = item.get('unit_price', 0)
                total = item.get('total_cost', 0)
                print(f"\n     - {name[:60]}")
                print(f"       Кол-во: {quantity} | Цена: {unit_price:,.0f} руб. | Итого: {total:,.0f} руб.")
        
        total_cost = validation.get('total_cost', 0)
        confidence = validation.get('confidence', 0)
        print(f"\n   💰 ИТОГО: {total_cost:,.0f} руб.")
        print(f"   🎯 Уверенность: {confidence * 100:.0f}%")
    
    print("\n" + "=" * 70)
    print(f"⏱️ ВРЕМЯ:")
    print(f"   Инициализация: {init_time:.2f}s")
    print(f"   Обработка запроса: {query_time:.2f}s")
    print(f"   Всего: {init_time + query_time:.2f}s")
    print("=" * 70)


if __name__ == "__main__":
    test_llm_mode_single_query()
