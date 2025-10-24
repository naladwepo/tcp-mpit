"""
Тест новой архитектуры: LLM на входе → поиск → ответ
"""

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine
from src.hybrid_processor import HybridQueryProcessor
import time


def test_new_architecture():
    """
    Тестирует новую архитектуру:
    1. LLM парсит запрос → список товаров + количество
    2. Поиск каждого товара
    3. Расчет стоимости и ответ
    """
    print("=" * 70)
    print("🚀 ТЕСТ НОВОЙ АРХИТЕКТУРЫ (LLM → ПОИСК → ОТВЕТ)")
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
    
    # Инициализация нового процессора
    print("\n🤖 Инициализация процессора с LLM парсером...")
    start_init = time.time()
    processor = HybridQueryProcessor(
        search_engine=search_engine,
        use_llm_parser=True,  # ✅ LLM парсер на входе
        use_fallback_enhancement=True
    )
    init_time = time.time() - start_init
    print(f"✓ Процессор готов (инициализация: {init_time:.2f}s)")
    
    # Тестовые запросы
    test_queries = [
        {
            "id": 1,
            "query": "Короб 200x200",
            "description": "Простой запрос"
        },
        {
            "id": 2,
            "query": "Комплект для монтажа короба: короб 200x200, крышка, 4 винта М6 и 4 гайки М6",
            "description": "Комплект с указанным количеством"
        },
        {
            "id": 3,
            "query": "Нужен лоток 600 мм с крышкой и крепежом",
            "description": "Набор без точного количества"
        }
    ]
    
    # Обработка запросов
    for test_case in test_queries:
        print("\n\n" + "="*70)
        print(f"ТЕСТОВЫЙ ЗАПРОС #{test_case['id']}")
        print(f"Описание: {test_case['description']}")
        print("="*70)
        
        start_query = time.time()
        result = processor.process_query(
            query=test_case['query'],
            top_k=3,  # Топ-3 результата на каждый товар
            query_id=test_case['id']
        )
        query_time = time.time() - start_query
        
        # Вывод результата
        print(f"\n{'='*70}")
        print(f"📊 ИТОГОВЫЙ ОТВЕТ")
        print(f"{'='*70}")
        print(f"Запрошено позиций: {result['total_items']}")
        print(f"Найдено позиций: {result['found_items']}")
        print(f"💰 Общая стоимость: {result['total_cost']:,.0f} руб.")
        print(f"⏱️  Время обработки: {query_time:.2f}s")
        
        # Детализация
        print(f"\n📋 ДЕТАЛИЗАЦИЯ ПО ПОЗИЦИЯМ:")
        print("-" * 70)
        for i, item in enumerate(result['items'], 1):
            print(f"\n{i}. Запрошено: {item['requested_item']}")
            print(f"   Количество: {item['quantity']} шт.")
            
            if item['found_product']:
                prod = item['found_product']
                print(f"   ✓ Найдено: {prod.get('name', 'N/A')[:60]}")
                print(f"   💰 {item['unit_price']:,.0f} руб. × {item['quantity']} = {item['total_price']:,.0f} руб.")
                print(f"   📊 Релевантность: {item['relevance_score']:.4f}")
                
                if item.get('alternatives'):
                    print(f"   📌 Альтернативы:")
                    for alt in item['alternatives'][:2]:
                        print(f"      - {alt['product'].get('name', 'N/A')[:50]} (score: {alt['score']:.4f})")
            else:
                print(f"   ❌ Товар не найден")
    
    print("\n\n" + "="*70)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("="*70)


def test_fallback_mode():
    """
    Тест fallback режима (без LLM, только QueryEnhancer)
    """
    print("\n\n" + "=" * 70)
    print("🔧 ТЕСТ FALLBACK РЕЖИМА (БЕЗ LLM)")
    print("=" * 70)
    
    # Загрузка данных
    data_loader = DataLoader()
    products = data_loader.get_products()
    
    # Поиск
    search_engine = VectorSearchEngine(
        model_name="intfloat/multilingual-e5-small",
        index_dir="data/index_e5"
    )
    search_engine.build_index(products)
    
    # Процессор БЕЗ LLM
    processor = HybridQueryProcessor(
        search_engine=search_engine,
        use_llm_parser=False,  # ❌ БЕЗ LLM
        use_fallback_enhancement=True
    )
    
    query = "Комплект: короб 200x200, крышка, винты М6"
    result = processor.process_query(query=query, top_k=2, query_id=99)
    
    print(f"\n💰 Итоговая стоимость: {result['total_cost']:,.0f} руб.")


if __name__ == "__main__":
    # Основной тест с LLM
    test_new_architecture()
    
    # Fallback тест без LLM
    # test_fallback_mode()
