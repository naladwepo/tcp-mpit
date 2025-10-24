#!/usr/bin/env python3
"""
Главный CLI интерфейс для RAG-системы поиска комплектующих

Использование:
    python main.py "Ваш запрос"
    python main.py --interactive
    python main.py --test test_queries.json
"""

import sys
import json
import argparse
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))


# Простой поисковый движок для fallback
class SimpleSearchEngine:
    """Простой поисковый движок на основе совпадения слов"""
    
    def __init__(self, products_df):
        self.products = products_df.to_dict('records')
    
    def search(self, query, top_k=10):
        """Простой текстовый поиск"""
        query_words = set(query.lower().split())
        scored_products = []
        
        for product in self.products:
            name = product.get('name', '').lower()
            category = product.get('category', '').lower()
            text = f"{name} {category}"
            
            score = sum(1 for word in query_words if word in text)
            if score > 0:
                scored_products.append((product, score))
        
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return scored_products[:top_k]


class SimpleProcessor:
    """Упрощенный процессор без векторного поиска"""
    
    def __init__(self, data_dir="."):
        from src.data_loader import DataLoader
        from src.cost_calculator import create_response_json
        
        self.loader = DataLoader(data_dir)
        self.df = self.loader.combine_datasets()
        self.search_engine = SimpleSearchEngine(self.df)
        self.create_response_json = create_response_json
    
    def process_query(self, query, complexity=None, query_id=None):
        """Обработка запроса"""
        results = self.search_engine.search(query, top_k=10)
        found_items = [product for product, score in results]
        
        return self.create_response_json(
            found_items=found_items,
            query_id=query_id,
            complexity=complexity
        )


def print_result(response: dict, show_details: bool = True):
    """
    Красиво выводит результат поиска
    
    Args:
        response: словарь с ответом
        show_details: показывать детали товаров
    """
    resp = response.get('response', {})
    
    print("\n" + "="*30)
    print("РЕЗУЛЬТАТЫ ПОИСКА")
    print("="*30)
    
    # Метаинформация
    if 'id' in response:
        print(f"ID запроса: {response['id']}")
    if 'complexity' in response:
        print(f"Сложность: {response['complexity']}")
    
    print(f"Найдено товаров: {resp.get('items_count', 0)}")
    print(f"Общая стоимость: {resp.get('total_cost', '0 руб.')}")
    
    # Список товаров
    if show_details:
        items = resp.get('found_items', [])
        if items:
            print("\nСписок товаров:")
            print("-"*30)
            for i, item in enumerate(items, 1):
                print(f"\n{i}. {item.get('name', 'Неизвестно')}")
                print(f"   Стоимость: {item.get('cost', '0 руб.')}")
    
    print("="*30 + "\n")


def interactive_mode(processor):
    """
    Интерактивный режим работы
    
    Args:
        processor: экземпляр процессора (QueryProcessor или SimpleProcessor)
    """
    print("\n" + "="*30)
    print("ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("="*30)
    print("Введите запрос для поиска товаров или 'exit' для выхода")
    print("Пример: Гайка М6")
    print("="*30 + "\n")
    
    while True:
        try:
            query = input("Запрос > ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("До свидания!")
                break
            
            # Обработка запроса
            response = processor.process_query(query)
            
            # Вывод результата
            print_result(response)
            
        except KeyboardInterrupt:
            print("\n\nДо свидания!")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}\n")


def process_test_file(processor, test_file: str):
    """
    Обрабатывает тестовый файл с запросами
    
    Args:
        processor: экземпляр процессора (QueryProcessor или SimpleProcessor)
        test_file: путь к JSON файлу с запросами
    """
    print(f"\nОбработка тестового файла: {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    query = test_data.get('query', '')
    query_id = test_data.get('id')
    complexity = test_data.get('complexity')
    
    print(f"\nЗапрос из файла: '{query}'")
    
    # Обработка
    response = processor.process_query(
        query=query,
        complexity=complexity,
        query_id=query_id
    )
    
    # Вывод
    print_result(response)
    
    # Сохраняем результат
    output_file = f"result_{Path(test_file).stem}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(response, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Результат сохранен в {output_file}")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='RAG-система поиска комплектующих и расчета стоимости'
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Поисковый запрос'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Интерактивный режим'
    )
    
    parser.add_argument(
        '-t', '--test',
        type=str,
        help='Путь к тестовому JSON файлу'
    )
    
    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='Отключить LLM (только векторный поиск)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='./Qwen/Qwen3-4B-Instruct-2507',
        help='Путь к модели Qwen'
    )
    
    parser.add_argument(
        '--embedding',
        type=str,
        default='sentence-transformers/all-MiniLM-L6-v2',
        help='Модель для эмбеддингов (по умолчанию: all-MiniLM-L6-v2)'
    )
    
    parser.add_argument(
        '--simple',
        action='store_true',
        help='Использовать простой текстовый поиск вместо векторного'
    )
    
    parser.add_argument(
        '--index-dir',
        type=str,
        default='data/index',
        help='Директория для хранения индекса'
    )
    
    parser.add_argument(
        '--rebuild-index',
        action='store_true',
        help='Пересоздать индекс даже если он существует'
    )
    
    args = parser.parse_args()
    
    # Выбираем режим поиска
    print("="*30)
    print("Инициализация RAG-системы поиска комплектующих")
    print("="*30)
    
    if args.simple:
        print("\n📝 Используется простой текстовый поиск\n")
        try:
            processor = SimpleProcessor(data_dir=".")
            print(f"✓ Система готова! Загружено {len(processor.df)} товаров\n")
        except Exception as e:
            print(f"❌ Не удалось инициализировать систему: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print("\n🔍 Используется векторный поиск\n")
        try:
            from src.data_loader import DataLoader
            from src.search_engine import VectorSearchEngine
            from src.hybrid_processor import HybridQueryProcessor
            
            # Загружаем данные
            data_loader = DataLoader()
            products_df = data_loader.get_products()
            print(f"✓ Загружено продуктов: {len(products_df)}")
            
            # Инициализируем векторный поиск
            search_engine = VectorSearchEngine(
                model_name=args.embedding,
                index_dir=args.index_dir
            )
            
            # Строим индекс если нужно
            if args.rebuild_index or not search_engine.load_index():
                print("🔨 Создание индекса...")
                search_engine.build_index(products_df, force_rebuild=args.rebuild_index)
                print("✓ Индекс создан и сохранен")
            else:
                print("✓ Индекс загружен")
            
            # Создаем гибридный процессор с LLM
            use_llm = not args.no_llm
            if use_llm:
                print("🤖 Инициализация LLM для препроцессинга...")
            
            processor = HybridQueryProcessor(
                search_engine=search_engine,
                use_llm=use_llm
            )
            print("✓ Векторный поиск готов к работе\n")
        except Exception as e:
            print(f"⚠️  Ошибка инициализации векторного поиска: {e}")
            print("📝 Переключение на простой текстовый поиск...\n")
            try:
                processor = SimpleProcessor(data_dir=".")
                print(f"✓ Система готова! Загружено {len(processor.df)} товаров\n")
            except Exception as e2:
                print(f"❌ Не удалось инициализировать систему: {e2}")
                import traceback
                traceback.print_exc()
                return 1
    
    # Выбор режима работы
    try:
        if args.interactive:
            # Интерактивный режим
            interactive_mode(processor)
        
        elif args.test:
            # Тестирование из файла
            process_test_file(processor, args.test)
        
        elif args.query:
            # Одиночный запрос
            response = processor.process_query(args.query)
            print_result(response)
            
            # Вывод JSON
            print("\nJSON ответ:")
            print(json.dumps(response, ensure_ascii=False, indent=2))
        
        else:
            # Если ничего не указано, показываем help
            parser.print_help()
            return 1
    
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
