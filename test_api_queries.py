#!/usr/bin/env python3
"""
Скрипт для тестирования API поиска через файлы запросов
Тестирует эндпоинт /search с запросами из JSON файлов
"""

import json
import requests
import time
from pathlib import Path
from typing import Dict, Any, List
from colorama import init, Fore, Style
import sys

# Инициализация colorama для цветного вывода
init(autoreset=True)

# Конфигурация
API_BASE_URL = "http://localhost:8000"
QUERY_FILES = [
    "query_1_simple.json",
    "query_2_simple.json",
    "query_4_medium.json",
    "query_5_medium.json",
    "query_8_complex.json"
]


class APITester:
    """Класс для тестирования API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results = []
        
    def check_health(self) -> bool:
        """Проверка здоровья API"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"{Fore.GREEN}✓ API доступен")
                print(f"  Статус: {health_data.get('status')}")
                print(f"  Модели загружены: {health_data.get('models_loaded')}")
                print(f"  Продуктов в базе: {health_data.get('products_count')}")
                print(f"  Модель эмбеддингов: {health_data.get('embedding_model')}")
                print(f"  LLM доступен: {health_data.get('llm_available')}")
                return health_data.get('status') == 'healthy'
            else:
                print(f"{Fore.RED}✗ API вернул статус {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}✗ Не удалось подключиться к API на {self.base_url}")
            print(f"{Fore.YELLOW}  Убедитесь, что сервер запущен: uvicorn src.api.main:app --reload")
            return False
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка при проверке health: {e}")
            return False
    
    def load_query_file(self, filename: str) -> Dict[str, Any]:
        """Загрузка файла с запросом"""
        filepath = Path(filename)
        if not filepath.exists():
            raise FileNotFoundError(f"Файл {filename} не найден")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def search(self, query: str, use_llm: bool = True) -> Dict[str, Any]:
        """Выполнение поиска через API"""
        url = f"{self.base_url}/search"
        payload = {
            "query": query,
            "use_llm": use_llm
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def compare_results(self, expected: Dict, actual: Dict) -> Dict[str, Any]:
        """Сравнение ожидаемых и фактических результатов"""
        comparison = {
            "query_match": False,
            "items_count_match": False,
            "found_items_match": False,
            "differences": []
        }
        
        # Проверяем запрос
        expected_query = expected.get('query', '')
        actual_query = actual.get('original_query', '')
        comparison["query_match"] = expected_query.lower() == actual_query.lower()
        
        # Проверяем количество найденных товаров
        expected_count = expected.get('response', {}).get('items_count', 0)
        actual_count = actual.get('found_items', 0)
        comparison["items_count_match"] = expected_count == actual_count
        
        if not comparison["items_count_match"]:
            comparison["differences"].append(
                f"Количество товаров: ожидалось {expected_count}, получено {actual_count}"
            )
        
        # Проверяем наличие найденных товаров
        expected_items = expected.get('response', {}).get('found_items', [])
        actual_items = actual.get('items', [])
        
        if len(expected_items) > 0 and len(actual_items) > 0:
            comparison["found_items_match"] = True
        
        return comparison
    
    def format_item(self, item: Dict[str, Any]) -> str:
        """Форматирование элемента результата для вывода"""
        product = item.get('found_product')
        if not product:
            return f"  ❌ Не найдено: {item.get('requested_item', 'Неизвестно')}"
        
        lines = [
            f"  📦 {item.get('requested_item', 'Товар')}",
            f"     Количество: {item.get('quantity', 1)} шт.",
            f"     Найдено: {product.get('name', 'Без названия')[:80]}...",
            f"     Цена за ед.: {item.get('unit_price', 0):.2f} руб.",
            f"     Итого: {item.get('total_price', 0):.2f} руб.",
            f"     Релевантность: {item.get('relevance_score', 0):.4f}"
        ]
        return "\n".join(lines)
    
    def test_query_file(self, filename: str) -> Dict[str, Any]:
        """Тестирование одного файла запроса"""
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}Тестирование: {filename}")
        print(f"{Fore.CYAN}{'=' * 70}")
        
        try:
            # Загружаем файл
            query_data = self.load_query_file(filename)
            query_id = query_data.get('id')
            complexity = query_data.get('complexity', 'unknown')
            query_text = query_data.get('query')
            
            print(f"{Fore.YELLOW}ID запроса: {query_id}")
            print(f"{Fore.YELLOW}Сложность: {complexity}")
            print(f"{Fore.YELLOW}Запрос: {query_text}")
            
            # Выполняем поиск
            start_time = time.time()
            result = self.search(query_text)
            elapsed_time = time.time() - start_time
            
            print(f"\n{Fore.GREEN}✓ Поиск выполнен за {elapsed_time:.2f} сек")
            
            # Выводим результаты
            print(f"\n{Fore.MAGENTA}Результаты поиска:")
            print(f"  Всего товаров в запросе: {result.get('total_items', 0)}")
            print(f"  Найдено товаров: {result.get('found_items', 0)}")
            print(f"  Общая стоимость: {result.get('total_cost', 0):.2f} {result.get('currency', 'RUB')}")
            
            print(f"\n{Fore.MAGENTA}Найденные товары:")
            for idx, item in enumerate(result.get('items', []), 1):
                print(f"\n{Fore.WHITE}[{idx}]")
                print(self.format_item(item))
            
            # Сравниваем с ожидаемыми результатами
            comparison = self.compare_results(query_data, result)
            
            print(f"\n{Fore.CYAN}Сравнение с ожидаемыми результатами:")
            if comparison["query_match"]:
                print(f"{Fore.GREEN}  ✓ Запрос совпадает")
            else:
                print(f"{Fore.RED}  ✗ Запрос не совпадает")
            
            if comparison["items_count_match"]:
                print(f"{Fore.GREEN}  ✓ Количество товаров совпадает")
            else:
                print(f"{Fore.YELLOW}  ⚠ Количество товаров отличается")
            
            for diff in comparison["differences"]:
                print(f"{Fore.YELLOW}  ⚠ {diff}")
            
            # Сохраняем результат
            test_result = {
                "filename": filename,
                "query_id": query_id,
                "complexity": complexity,
                "query": query_text,
                "execution_time": elapsed_time,
                "result": result,
                "comparison": comparison,
                "success": True
            }
            
            self.results.append(test_result)
            return test_result
            
        except FileNotFoundError as e:
            print(f"{Fore.RED}✗ Ошибка: {e}")
            self.results.append({
                "filename": filename,
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
            
        except requests.exceptions.HTTPError as e:
            print(f"{Fore.RED}✗ HTTP ошибка: {e}")
            print(f"{Fore.RED}  Ответ сервера: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            self.results.append({
                "filename": filename,
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
            
        except Exception as e:
            print(f"{Fore.RED}✗ Неожиданная ошибка: {e}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "filename": filename,
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    def save_results(self, output_file: str = "api_test_results.json"):
        """Сохранение результатов тестирования"""
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n{Fore.GREEN}✓ Результаты сохранены в {output_file}")
    
    def print_summary(self):
        """Вывод итоговой статистики"""
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}ИТОГОВАЯ СТАТИСТИКА")
        print(f"{Fore.CYAN}{'=' * 70}")
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('success', False))
        failed = total - successful
        
        print(f"\n{Fore.WHITE}Всего тестов: {total}")
        print(f"{Fore.GREEN}Успешных: {successful}")
        print(f"{Fore.RED}Неудачных: {failed}")
        
        if successful > 0:
            avg_time = sum(r.get('execution_time', 0) for r in self.results if r.get('success')) / successful
            print(f"{Fore.YELLOW}Среднее время выполнения: {avg_time:.2f} сек")
        
        # Статистика по сложности
        complexity_stats = {}
        for r in self.results:
            if r.get('success'):
                complexity = r.get('complexity', 'unknown')
                if complexity not in complexity_stats:
                    complexity_stats[complexity] = {'count': 0, 'total_time': 0}
                complexity_stats[complexity]['count'] += 1
                complexity_stats[complexity]['total_time'] += r.get('execution_time', 0)
        
        if complexity_stats:
            print(f"\n{Fore.MAGENTA}Статистика по сложности:")
            for complexity, stats in sorted(complexity_stats.items()):
                avg = stats['total_time'] / stats['count']
                print(f"  {complexity}: {stats['count']} тестов, среднее время {avg:.2f} сек")


def main():
    """Главная функция"""
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("=" * 70)
    print("  ТЕСТИРОВАНИЕ API ПОИСКА КОМПЛЕКТУЮЩИХ")
    print("=" * 70)
    print(Style.RESET_ALL)
    
    # Создаем тестер
    tester = APITester()
    
    # Проверяем доступность API
    print(f"\n{Fore.YELLOW}Проверка доступности API...")
    if not tester.check_health():
        print(f"\n{Fore.RED}API недоступен. Запустите сервер и попробуйте снова.")
        sys.exit(1)
    
    # Запрашиваем подтверждение
    print(f"\n{Fore.YELLOW}Будут протестированы следующие файлы:")
    for idx, filename in enumerate(QUERY_FILES, 1):
        print(f"  {idx}. {filename}")
    
    response = input(f"\n{Fore.CYAN}Начать тестирование? (y/n): {Style.RESET_ALL}")
    if response.lower() not in ['y', 'yes', 'д', 'да']:
        print(f"{Fore.YELLOW}Тестирование отменено.")
        sys.exit(0)
    
    # Тестируем каждый файл
    for filename in QUERY_FILES:
        tester.test_query_file(filename)
        time.sleep(0.5)  # Небольшая пауза между запросами
    
    # Выводим итоговую статистику
    tester.print_summary()
    
    # Сохраняем результаты
    tester.save_results()
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Тестирование завершено!{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
