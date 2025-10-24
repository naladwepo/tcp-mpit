#!/usr/bin/env python3
"""
Тест гибридного процессора
"""

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine
from src.hybrid_processor import HybridQueryProcessor

# Загружаем данные
print("Загрузка данных...")
data_loader = DataLoader()
products_df = data_loader.get_products()

# Инициализируем векторный поиск
print("Инициализация векторного поиска...")
search_engine = VectorSearchEngine(
    model_name='./sentence-transformers/paraphrase-multilingual-mpnet-base-v2/paraphrase-multilingual-mpnet-base-v2',
    index_dir='data/index_multilingual'
)
search_engine.load_index()

# Создаем гибридный процессор
processor = HybridQueryProcessor(search_engine)

# Тестируем
query = 'Комплект для монтажа короба 200x200: короб, крышка, винты и гайки'
print(f"\nЗапрос: {query}\n")

result = processor.process_query(query, complexity='complex', query_id=8)

print('=== РЕЗУЛЬТАТЫ ГИБРИДНОГО ПОИСКА ===')
print(f"Найдено товаров: {result['response']['items_count']}")
print(f"Общая стоимость: {result['response']['total_cost']}")
print('\nТовары:')
for i, item in enumerate(result['response']['found_items'], 1):
    name = item['name'][:70]
    cost = item['cost']
    print(f"{i}. {name}")
    print(f"   {cost}")
