"""
Отладочный скрипт для проверки структуры данных
"""

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine

# Загрузка данных
print("Загрузка данных...")
data_loader = DataLoader()
products = data_loader.get_products()

print(f"\nКолонки DataFrame: {products.columns.tolist()}")
print(f"\nПервая строка DataFrame:")
print(products.iloc[0])

# Инициализация поиска
print("\n" + "="*70)
print("Инициализация поиска...")
search_engine = VectorSearchEngine(
    model_name="intfloat/multilingual-e5-small",
    index_dir="data/index_e5"
)
search_engine.build_index(products)

# Поиск
print("\n" + "="*70)
print("Тестовый поиск...")
results = search_engine.search("Гайка М6", top_k=3)

print(f"\nНайдено результатов: {len(results)}")
for i, (product, score) in enumerate(results, 1):
    print(f"\n--- Результат #{i} ---")
    print(f"Тип: {type(product)}")
    print(f"Ключи: {product.keys() if isinstance(product, dict) else 'N/A'}")
    print(f"Содержимое:")
    if isinstance(product, dict):
        for key, value in product.items():
            print(f"  {key}: {value}")
    else:
        print(f"  {product}")
    print(f"Score: {score}")
