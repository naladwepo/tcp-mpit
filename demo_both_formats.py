#!/usr/bin/env python3
"""
ДЕМО: Генерация ТКП в форматах DOCX и PDF
"""

from src.document_generator import DocumentGenerator

# Пример данных
example_data = {
    "original_query": "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки",
    "items": [
        {
            "requested_item": "Короб 200x200",
            "quantity": 2,
            "found_product": {
                "name": "Короб 200x200 мм, L=2000 мм, горячее цинкование, толщина покрытия не менее 80 мкм",
                "cost": 88498.0
            },
            "specifications": "200x200 мм, L=2000 мм",
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
            "specifications": "200 мм, L=2000 мм",
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
            "specifications": "М6х10",
            "unit_price": 100.0,
            "total_price": 2000.0
        },
        {
            "requested_item": "Гайки для монтажа",
            "quantity": 20,
            "found_product": {
                "name": "Гайка М6, оцинкованная",
                "cost": 50.0
            },
            "specifications": "М6",
            "unit_price": 50.0,
            "total_price": 1000.0
        }
    ]
}

def main():
    """Генерация документов в обоих форматах"""
    
    print("=" * 70)
    print("  ГЕНЕРАЦИЯ ТКП: DOCX и PDF")
    print("=" * 70)
    print()
    
    # Создаем генератор
    print("📄 Инициализация генератора документов...")
    generator = DocumentGenerator(output_dir="generated_documents")
    print("✓ Генератор готов")
    print()
    
    # Информация о запросе
    total_cost = sum(item['total_price'] for item in example_data['items'])
    print("📊 Данные для ТКП:")
    print(f"  Запрос: {example_data['original_query']}")
    print(f"  Товаров: {len(example_data['items'])}")
    print(f"  Общая стоимость: {total_cost:,.2f} ₽")
    print()
    
    # Генерируем оба формата
    print("📝 Генерация документов...")
    print()
    
    try:
        files = generator.generate_both(example_data, "komplekt_tkp")
        
        print("✅ Документы успешно созданы:")
        print()
        
        # Word
        word_file = files['word']
        if word_file.exists():
            print(f"📄 Word документ:")
            print(f"   Файл: {word_file.name}")
            print(f"   Путь: {word_file}")
            print(f"   Размер: {word_file.stat().st_size / 1024:.1f} KB")
            print()
        
        # PDF
        pdf_file = files['pdf']
        if pdf_file.exists():
            print(f"📕 PDF документ:")
            print(f"   Файл: {pdf_file.name}")
            print(f"   Путь: {pdf_file}")
            print(f"   Размер: {pdf_file.stat().st_size / 1024:.1f} KB")
            print()
        
        print("=" * 70)
        print("✅ Генерация завершена успешно!")
        print()
        print("💡 Откройте файлы для просмотра:")
        print(f"   open {word_file}")
        print(f"   open {pdf_file}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка при генерации: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
