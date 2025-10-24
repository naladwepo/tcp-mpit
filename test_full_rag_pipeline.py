"""
Тест полного RAG pipeline с LLM валидацией
"""

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine
from src.hybrid_processor import HybridQueryProcessor


def test_full_pipeline():
    """
    Тестирует полный pipeline:
    1. Query Enhancement
    2. Vector Search
    3. LLM Validation (с расчётом количества и стоимости)
    """
    print("=" * 70)
    print("🚀 ТЕСТ ПОЛНОГО RAG PIPELINE")
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
    
    # Инициализация гибридного процессора с валидатором
    print("\n🤖 Инициализация гибридного процессора...")
    processor = HybridQueryProcessor(
        search_engine=search_engine,
        use_llm=True,  # ✅ ВКЛЮЧАЕМ LLM-режим для тестирования
        use_query_enhancement=True,
        use_llm_validator=True,  # Включаем валидатор
        use_iterative_search=False  # Пока без итеративного поиска
    )
    print("✓ Процессор готов (LLM-режим активирован)")
    
    # Тестовые запросы
    test_queries = [
        {
            "id": 1,
            "query": "Гайка М6",
            "complexity": "simple"
        },
        {
            "id": 2,
            "query": "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки",
            "complexity": "complex"
        },
        {
            "id": 3,
            "query": "Лоток перфорированный 600 мм с крепежом",
            "complexity": "medium"
        }
    ]
    
    # Обработка запросов
    for test_query in test_queries:
        print("\n" + "=" * 70)
        print(f"📋 ЗАПРОС #{test_query['id']}")
        print("=" * 70)
        print(f"Query: {test_query['query']}")
        print(f"Complexity: {test_query['complexity']}")
        print("-" * 70)
        
        result = processor.process_query(
            query=test_query['query'],
            top_k=10,
            complexity=test_query['complexity'],
            query_id=test_query['id'],
            use_validation=True  # Включаем валидацию
        )
        
        # Выводим краткую сводку
        print("\n📊 КРАТКАЯ СВОДКА:")
        print(f"  • Найдено товаров: {result['retrieval_results']['total_found']}")
        print(f"  • Выбрано после валидации: {len(result['final_selection'])}")
        print(f"  • Общая стоимость: {result['total_cost']:,} руб.")
        print(f"  • Уверенность: {result['confidence']:.0%}")
        
        if result.get('missing_items'):
            print(f"  ⚠️ Не хватает: {len(result['missing_items'])} позиций")
        
        print("\n✅ ВЫБРАННЫЕ ТОВАРЫ:")
        for item in result['final_selection']:
            print(f"  • {item['name']} × {item['quantity']} = {item['total_price']:,} руб.")


def test_with_iterative_search():
    """
    Тест с итеративным поиском (если чего-то не хватает)
    """
    print("\n\n" + "=" * 70)
    print("🔄 ТЕСТ ИТЕРАТИВНОГО ПОИСКА")
    print("=" * 70)
    
    # Загрузка данных
    print("\n📦 Загрузка данных...")
    data_loader = DataLoader()
    products = data_loader.get_products()
    
    # Инициализация векторного поиска
    print("🔍 Инициализация векторного поиска...")
    search_engine = VectorSearchEngine(
        model_name="intfloat/multilingual-e5-small",
        index_dir="data/index_e5"
    )
    search_engine.build_index(products)
    
    # Инициализация с итеративным поиском
    print("🤖 Инициализация с итеративным поиском...")
    processor = HybridQueryProcessor(
        search_engine=search_engine,
        use_llm=True,  # ✅ ВКЛЮЧАЕМ LLM-режим
        use_query_enhancement=True,
        use_llm_validator=True,
        use_iterative_search=True  # Включаем итеративный поиск!
    )
    
    # Тестовый запрос с неполными результатами
    query = "Полный комплект для монтажа: короб 200x200, крышка, винты М6, гайки М6, шайбы М6"
    
    print(f"\n📋 ЗАПРОС: {query}")
    print("-" * 70)
    
    result = processor.process_query(
        query=query,
        top_k=5,  # Специально мало, чтобы проверить итеративный поиск
        complexity="complex",
        query_id=99,
        use_validation=True
    )
    
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print(f"  • Итераций поиска: {result['validation'].get('iterations', 1)}")
    print(f"  • Всего найдено товаров: {result['validation'].get('total_items_found', 0)}")
    print(f"  • Выбрано: {len(result['final_selection'])}")
    print(f"  • Общая стоимость: {result['total_cost']:,} руб.")


if __name__ == "__main__":
    # Тест 1: Основной pipeline
    test_full_pipeline()
    
    # Тест 2: Итеративный поиск (раскомментируйте если хотите протестировать)
    # test_with_iterative_search()
    
    print("\n" + "=" * 70)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 70)
