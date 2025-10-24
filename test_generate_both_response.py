#!/usr/bin/env python3
"""
Тест нового формата ответа /generate/both
Теперь возвращается информация о файлах + результат поиска строкой
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_generate_both_with_result():
    """Тест генерации с результатом в строке"""
    
    print("=" * 70)
    print("  ТЕСТ: /generate/both с результатом поиска")
    print("=" * 70)
    print()
    
    # Проверяем API
    print("🔍 Проверка API...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("✗ API недоступен")
            return
        print("✓ API доступен")
    except:
        print("✗ API не запущен!")
        print("  Запустите: uvicorn src.api.main:app --reload")
        return
    
    print()
    
    # Тестовый запрос
    query = "Короб 200x200 и крышка"
    
    print(f"📝 Запрос: {query}")
    print()
    print("🔄 Генерация документов и получение результата...")
    print()
    
    try:
        response = requests.post(
            f"{API_URL}/generate/both",
            json={"query": query, "use_llm": True},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("=" * 70)
            print("✅ ОТВЕТ ПОЛУЧЕН")
            print("=" * 70)
            print()
            
            # 1. Информация о файлах
            print("📁 ФАЙЛЫ:")
            print(f"   Word: {result['files']['word']['filename']}")
            print(f"   PDF:  {result['files']['pdf']['filename']}")
            print()
            
            # 2. Краткая статистика
            print("📊 СТАТИСТИКА:")
            search_data = result.get('search_data', {})
            print(f"   Запрос: {search_data.get('original_query')}")
            print(f"   Всего товаров: {search_data.get('total_items')}")
            print(f"   Найдено: {search_data.get('found_items')}")
            print(f"   Стоимость: {search_data.get('total_cost'):,.2f} {search_data.get('currency')}")
            print()
            
            # 3. Полный результат строкой
            print("📄 РЕЗУЛЬТАТ ПОИСКА (СТРОКА):")
            print()
            print(result.get('search_result', 'Нет данных'))
            print()
            
            # Сохраняем результат в файл
            result_file = "api_response.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print("=" * 70)
            print(f"✅ Полный ответ сохранен в: {result_file}")
            print()
            
            # Сохраняем строку результата отдельно
            text_file = "search_result.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(result.get('search_result', ''))
            
            print(f"✅ Результат поиска (текст) сохранен в: {text_file}")
            print()
            
        else:
            print(f"✗ Ошибка: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_generate_both_with_result()
