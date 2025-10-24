"""
Быстрый тест проверки цен с эвристической валидацией
"""

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine
from src.hybrid_processor import HybridQueryProcessor


def test_prices_heuristic():
    """
    Тестирует, что цены корректно берутся из столбца 'Цена' (теперь 'cost')
    Использует быструю эвристическую валидацию вместо LLM
    """
    print("=" * 70)
    print("🚀 ТЕСТ ЦЕНЫ С ЭВРИСТИЧЕСКОЙ ВАЛИДАЦИЕЙ")
    print("=" * 70)
    
    # Загрузка данных
    print("\n📦 Загрузка данных...")
    data_loader = DataLoader()
    products = data_loader.get_products()
    print(f"✓ Загружено {len(products)} товаров")
    
    # Проверка, что цены загрузились
    print("\n💰 Проверка загруженных цен:")
    products_with_cost = products[products['cost'] > 0]
    products_zero_cost = products[products['cost'] == 0]
    print(f"  Товаров с ценой > 0: {len(products_with_cost)}")
    print(f"  Товаров с ценой = 0: {len(products_zero_cost)}")
    
    if len(products_with_cost) > 0:
        print(f"\n  Примеры товаров с ценами:")
        for idx, row in products_with_cost.head(5).iterrows():
            print(f"    - {row['name'][:50]}: {row['cost']} руб.")
    
    # Инициализация векторного поиска
    print("\n🔍 Инициализация векторного поиска...")
    search_engine = VectorSearchEngine(
        model_name="intfloat/multilingual-e5-small",
        index_dir="data/index_e5"
    )
    search_engine.build_index(products)
    print("✓ Векторный поиск готов")
    
    # Инициализация гибридного процессора БЕЗ LLM (быстрый режим)
    print("\n🤖 Инициализация процессора (эвристический режим)...")
    processor = HybridQueryProcessor(
        search_engine=search_engine,
        use_llm=False,  # Быстрый режим без LLM
        use_query_enhancement=True,
        use_llm_validator=True,  # Валидатор работает в эвристическом режиме
        use_iterative_search=False
    )
    print("✓ Процессор готов (эвристический режим)")
    
    # Тестовые запросы
    test_queries = [
        {
            "id": 1,
            "query": "Гайка М6",
            "complexity": "simple",
            "description": "Простой запрос: крепёж"
        },
        {
            "id": 2,
            "query": "Короб 200x200",
            "complexity": "medium",
            "description": "Средний запрос: кабельный канал"
        },
        {
            "id": 3,
            "query": "Комплект для монтажа короба: короб, крышка, 4 винта М6",
            "complexity": "complex",
            "description": "Сложный запрос: комплект с количеством"
        }
    ]
    
    # Обработка запросов
    for test_case in test_queries:
        print("\n" + "=" * 70)
        print(f"📋 ЗАПРОС #{test_case['id']}")
        print("=" * 70)
        print(f"Query: {test_case['query']}")
        print(f"Complexity: {test_case['complexity']}")
        print(f"Description: {test_case['description']}")
        print("-" * 70)
        
        result = processor.process_query(
            query=test_case['query'],
            top_k=5,
            complexity=test_case['complexity'],
            query_id=test_case['id'],
            use_validation=True
        )
        
        print("\n📊 РЕЗУЛЬТАТЫ:")
        print(f"Всего найдено: {result.get('total_items', 0)} товаров")
        
        # Результаты поиска
        if 'results' in result and result['results']:
            print(f"\n🔍 Топ-{len(result['results'])} результатов:")
            for i, item in enumerate(result['results'][:5], 1):
                product = item['product']
                score = item['score']
                cost = product.get('cost', 0)
                print(f"\n  {i}. {product.get('name', 'N/A')[:60]}")
                print(f"     Релевантность: {score:.4f}")
                print(f"     💰 Цена за ед.: {cost:,.2f} руб.")
                print(f"     Категория: {product.get('category', 'N/A')}")
        
        # Результат валидации
        if 'validation' in result and result['validation']:
            validation = result['validation']
            print(f"\n✅ ВАЛИДАЦИЯ (режим: {validation.get('mode', 'unknown')}):")
            print(f"   Статус: {validation.get('status', 'N/A')}")
            print(f"   Найдено позиций: {len(validation.get('items', []))}")
            
            if 'items' in validation:
                print("\n   📦 Детализация по позициям:")
                for item in validation['items']:
                    name = item.get('name', 'N/A')
                    quantity = item.get('quantity', 0)
                    unit_price = item.get('unit_price', 0)
                    total = item.get('total_cost', 0)
                    print(f"\n     - {name[:50]}")
                    print(f"       Количество: {quantity} шт.")
                    print(f"       💰 Цена за ед.: {unit_price:,.2f} руб.")
                    print(f"       💰 Итого: {total:,.2f} руб.")
            
            total_cost = validation.get('total_cost', 0)
            print(f"\n   💰 ИТОГОВАЯ СТОИМОСТЬ: {total_cost:,.2f} руб.")
        
        print("\n" + "-" * 70)


if __name__ == "__main__":
    test_prices_heuristic()
