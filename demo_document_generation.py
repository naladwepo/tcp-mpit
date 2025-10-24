#!/usr/bin/env python3
"""
ДЕМО: Генерация ТКП документа
Простой пример использования генератора документов
"""

from src.document_generator import DocumentGenerator

# Пример данных из поиска
example_data = {
    "original_query": "Комплект для монтажа короба 200x200: короб, крышка, винты",
    "items": [
        {
            "requested_item": "Короб 200x200",
            "quantity": 2,
            "found_product": {
                "name": "Короб 200x200 мм, L=2000 мм, горячее цинкование, толщина покрытия не менее 80 мкм",
                "cost": 88498.0
            },
            "specifications": "200x200 мм, длина 2000 мм",
            "unit_price": 88498.0,
            "total_price": 176996.0
        },
        {
            "requested_item": "Крышка для короба 200x200",
            "quantity": 2,
            "found_product": {
                "name": "Крышка 200 мм, L=2000 мм, горячее цинкование, толщина покрытия не менее 80 мкм",
                "cost": 45131.0
            },
            "specifications": "200 мм, длина 2000 мм",
            "unit_price": 45131.0,
            "total_price": 90262.0
        },
        {
            "requested_item": "Винты для монтажа",
            "quantity": 20,
            "found_product": {
                "name": "Винт с крестообразным шлицем М6х10",
                "cost": 100.0
            },
            "specifications": "М6х10, оцинкованный",
            "unit_price": 100.0,
            "total_price": 2000.0
        }
    ]
}

def main():
    """Демонстрация генерации документов"""
    
    print("=" * 70)
    print("  ДЕМО: Генерация ТКП документа")
    print("=" * 70)
    print()
    
    # Создаем генератор
    print("📄 Инициализация генератора...")
    generator = DocumentGenerator(output_dir="generated_documents")
    print("✓ Генератор готов")
    print()
    
    # Генерируем Word документ
    print("📝 Генерация Word документа...")
    word_file = generator.generate_word(example_data, "demo_tkp.docx")
    print(f"✓ Word документ создан: {word_file}")
    print(f"  Размер: {word_file.stat().st_size / 1024:.1f} KB")
    print()
    
    # Информация о содержимом
    print("📊 Содержимое документа:")
    print(f"  Запрос: {example_data['original_query']}")
    print(f"  Товаров: {len(example_data['items'])}")
    
    total_cost = sum(item['total_price'] for item in example_data['items'])
    print(f"  Общая стоимость: {total_cost:,.2f} ₽")
    print()
    
    print("=" * 70)
    print("✅ Демо завершено!")
    print()
    print("📁 Документ находится в: generated_documents/demo_tkp.docx")
    print("💡 Откройте файл в Word/LibreOffice для просмотра")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
