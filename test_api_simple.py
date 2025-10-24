#!/usr/bin/env python3
"""
Упрощенный скрипт для тестирования API поиска через файлы запросов
Без зависимости от colorama - работает везде
"""

import json
import requests
import time
from pathlib import Path
from typing import Dict, Any
import sys


# Конфигурация
API_BASE_URL = "http://localhost:8000"
QUERY_FILES = [
    "query_1_simple.json",
    "query_2_simple.json",
    "query_4_medium.json",
    "query_5_medium.json",
    "query_8_complex.json"
]


def check_api_health(base_url: str) -> bool:
    """Проверка здоровья API"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✓ API доступен")
            print(f"  Статус: {health_data.get('status')}")
            print(f"  Модели загружены: {health_data.get('models_loaded')}")
            print(f"  Продуктов в базе: {health_data.get('products_count')}")
            print(f"  Модель эмбеддингов: {health_data.get('embedding_model')}")
            print(f"  LLM доступен: {health_data.get('llm_available')}")
            return health_data.get('status') == 'healthy'
        else:
            print(f"✗ API вернул статус {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Не удалось подключиться к API на {base_url}")
        print("  Убедитесь, что сервер запущен: uvicorn src.api.main:app --reload")
        return False
    except Exception as e:
        print(f"✗ Ошибка при проверке health: {e}")
        return False


def load_query_file(filename: str) -> Dict[str, Any]:
    """Загрузка файла с запросом"""
    filepath = Path(filename)
    if not filepath.exists():
        raise FileNotFoundError(f"Файл {filename} не найден")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_via_api(base_url: str, query: str, use_llm: bool = True) -> Dict[str, Any]:
    """Выполнение поиска через API"""
    url = f"{base_url}/search"
    payload = {
        "query": query,
        "use_llm": use_llm
    }
    
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def format_result_item(item: Dict[str, Any], index: int) -> str:
    """Форматирование элемента результата"""
    product = item.get('found_product')
    
    lines = [f"\n[{index}] {item.get('requested_item', 'Товар')}"]
    lines.append(f"    Количество: {item.get('quantity', 1)} шт.")
    
    if product:
        name = product.get('name', 'Без названия')
        # Обрезаем длинное название
        if len(name) > 100:
            name = name[:100] + "..."
        lines.append(f"    Найдено: {name}")
        lines.append(f"    Цена за ед.: {item.get('unit_price', 0):.2f} руб.")
        lines.append(f"    Итого: {item.get('total_price', 0):.2f} руб.")
        lines.append(f"    Релевантность: {item.get('relevance_score', 0):.4f}")
    else:
        lines.append(f"    ❌ Товар не найден")
    
    return "\n".join(lines)


def test_query_file(base_url: str, filename: str) -> Dict[str, Any]:
    """Тестирование одного файла запроса"""
    print("\n" + "=" * 70)
    print(f"Тестирование: {filename}")
    print("=" * 70)
    
    try:
        # Загружаем файл
        query_data = load_query_file(filename)
        query_id = query_data.get('id')
        complexity = query_data.get('complexity', 'unknown')
        query_text = query_data.get('query')
        
        print(f"ID запроса: {query_id}")
        print(f"Сложность: {complexity}")
        print(f"Запрос: {query_text}")
        
        # Выполняем поиск
        print("\nВыполняем поиск...")
        start_time = time.time()
        result = search_via_api(base_url, query_text)
        elapsed_time = time.time() - start_time
        
        print(f"✓ Поиск выполнен за {elapsed_time:.2f} сек")
        
        # Выводим результаты
        print(f"\nРезультаты поиска:")
        print(f"  Всего товаров в запросе: {result.get('total_items', 0)}")
        print(f"  Найдено товаров: {result.get('found_items', 0)}")
        print(f"  Общая стоимость: {result.get('total_cost', 0):.2f} {result.get('currency', 'RUB')}")
        
        print(f"\nНайденные товары:")
        for idx, item in enumerate(result.get('items', []), 1):
            print(format_result_item(item, idx))
        
        # Сравниваем с ожидаемыми результатами
        expected_count = query_data.get('response', {}).get('items_count', 0)
        actual_count = result.get('found_items', 0)
        
        print(f"\nСравнение с ожидаемыми результатами:")
        print(f"  Ожидалось товаров: {expected_count}")
        print(f"  Найдено товаров: {actual_count}")
        if expected_count == actual_count:
            print("  ✓ Количество совпадает")
        else:
            print(f"  ⚠ Количество отличается (разница: {actual_count - expected_count})")
        
        return {
            "filename": filename,
            "query_id": query_id,
            "complexity": complexity,
            "query": query_text,
            "execution_time": elapsed_time,
            "expected_count": expected_count,
            "actual_count": actual_count,
            "total_cost": result.get('total_cost', 0),
            "success": True,
            "result": result
        }
        
    except FileNotFoundError as e:
        print(f"✗ Ошибка: {e}")
        return {"filename": filename, "success": False, "error": str(e)}
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP ошибка: {e}")
        if hasattr(e, 'response'):
            print(f"  Ответ сервера: {e.response.text}")
        return {"filename": filename, "success": False, "error": str(e)}
        
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return {"filename": filename, "success": False, "error": str(e)}


def save_results(results: list, output_file: str = "api_test_results.json"):
    """Сохранение результатов тестирования"""
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Результаты сохранены в {output_file}")


def print_summary(results: list):
    """Вывод итоговой статистики"""
    print("\n" + "=" * 70)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    
    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    failed = total - successful
    
    print(f"\nВсего тестов: {total}")
    print(f"Успешных: {successful}")
    print(f"Неудачных: {failed}")
    
    if successful > 0:
        avg_time = sum(r.get('execution_time', 0) for r in results if r.get('success')) / successful
        total_cost = sum(r.get('total_cost', 0) for r in results if r.get('success'))
        print(f"Среднее время выполнения: {avg_time:.2f} сек")
        print(f"Общая стоимость по всем запросам: {total_cost:.2f} руб.")
        
        # Детальная статистика
        print("\nДетальная статистика:")
        for r in results:
            if r.get('success'):
                print(f"  {r['filename']}: {r['execution_time']:.2f} сек, "
                      f"{r['actual_count']} товаров, {r['total_cost']:.2f} руб.")
    
    # Статистика по сложности
    complexity_stats = {}
    for r in results:
        if r.get('success'):
            complexity = r.get('complexity', 'unknown')
            if complexity not in complexity_stats:
                complexity_stats[complexity] = {'count': 0, 'total_time': 0}
            complexity_stats[complexity]['count'] += 1
            complexity_stats[complexity]['total_time'] += r.get('execution_time', 0)
    
    if complexity_stats:
        print("\nСтатистика по сложности:")
        for complexity, stats in sorted(complexity_stats.items()):
            avg = stats['total_time'] / stats['count']
            print(f"  {complexity}: {stats['count']} тестов, среднее время {avg:.2f} сек")


def main():
    """Главная функция"""
    print("=" * 70)
    print("  ТЕСТИРОВАНИЕ API ПОИСКА КОМПЛЕКТУЮЩИХ")
    print("=" * 70)
    
    # Проверяем доступность API
    print("\nПроверка доступности API...")
    if not check_api_health(API_BASE_URL):
        print("\nAPI недоступен. Запустите сервер и попробуйте снова.")
        print("Команда для запуска: uvicorn src.api.main:app --reload")
        sys.exit(1)
    
    # Показываем список файлов для тестирования
    print(f"\nБудут протестированы следующие файлы:")
    for idx, filename in enumerate(QUERY_FILES, 1):
        print(f"  {idx}. {filename}")
    
    # Тестируем каждый файл
    results = []
    for filename in QUERY_FILES:
        result = test_query_file(API_BASE_URL, filename)
        results.append(result)
        time.sleep(0.5)  # Небольшая пауза между запросами
    
    # Выводим итоговую статистику
    print_summary(results)
    
    # Сохраняем результаты
    save_results(results)
    
    print("\n✅ Тестирование завершено!\n")


if __name__ == "__main__":
    main()
