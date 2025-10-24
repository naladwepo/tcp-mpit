#!/usr/bin/env python3
"""
Тестовый скрипт для генерации ТКП документов через API
"""

import requests
import json
from pathlib import Path

# Конфигурация
API_BASE_URL = "http://localhost:8000"

# Тестовые запросы
TEST_QUERIES = [
    "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки",
    "Крышка 200 мм",
    "Гайка М6"
]


def check_api():
    """Проверка доступности API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API доступен")
            return True
        return False
    except:
        print("✗ API недоступен")
        return False


def generate_word(query: str):
    """Генерация Word документа"""
    print(f"\n📄 Генерация Word документа...")
    print(f"   Запрос: {query}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate/word",
            json={"query": query, "use_llm": True},
            timeout=120
        )
        
        if response.status_code == 200:
            # Сохраняем файл
            filename = f"test_tkp_{query[:20].replace(' ', '_')}.docx"
            filepath = Path(filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"   ✓ Word документ сохранен: {filepath}")
            return filepath
        else:
            print(f"   ✗ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return None


def generate_pdf(query: str):
    """Генерация PDF документа"""
    print(f"\n📄 Генерация PDF документа...")
    print(f"   Запрос: {query}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate/pdf",
            json={"query": query, "use_llm": True},
            timeout=120
        )
        
        if response.status_code == 200:
            # Определяем расширение файла из Content-Type
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type:
                ext = 'pdf'
            else:
                ext = 'docx'
            
            # Сохраняем файл
            filename = f"test_tkp_{query[:20].replace(' ', '_')}.{ext}"
            filepath = Path(filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            if ext == 'pdf':
                print(f"   ✓ PDF документ сохранен: {filepath}")
            else:
                print(f"   ⚠ PDF недоступен, сохранен Word: {filepath}")
            return filepath
        else:
            print(f"   ✗ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return None


def generate_both(query: str):
    """Генерация обоих форматов"""
    print(f"\n📄 Генерация обоих форматов...")
    print(f"   Запрос: {query}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate/both",
            json={"query": query, "use_llm": True},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Документы созданы:")
            print(f"     Word: {result['files']['word']['filename']}")
            print(f"     PDF: {result['files']['pdf']['filename']}")
            print(f"     Скачать: {API_BASE_URL}{result['files']['word']['download_url']}")
            print(f"     Скачать: {API_BASE_URL}{result['files']['pdf']['download_url']}")
            return result
        else:
            print(f"   ✗ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return None


def main():
    """Главная функция"""
    print("=" * 70)
    print("  ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ ТКП ДОКУМЕНТОВ")
    print("=" * 70)
    
    # Проверяем API
    if not check_api():
        print("\nЗапустите API: uvicorn src.api.main:app --reload")
        return
    
    # Выбираем запрос
    print("\nВыберите тестовый запрос:")
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"  {i}. {query}")
    print(f"  {len(TEST_QUERIES) + 1}. Свой запрос")
    
    try:
        choice = int(input("\nВыбор: "))
        
        if 1 <= choice <= len(TEST_QUERIES):
            query = TEST_QUERIES[choice - 1]
        elif choice == len(TEST_QUERIES) + 1:
            query = input("Введите запрос: ")
        else:
            print("Неверный выбор")
            return
    except:
        print("Неверный ввод")
        return
    
    # Выбираем формат
    print("\nВыберите формат:")
    print("  1. Word (.docx)")
    print("  2. PDF")
    print("  3. Оба формата")
    
    try:
        format_choice = int(input("Выбор: "))
    except:
        print("Неверный ввод")
        return
    
    # Генерируем
    if format_choice == 1:
        generate_word(query)
    elif format_choice == 2:
        generate_pdf(query)
    elif format_choice == 3:
        generate_both(query)
    else:
        print("Неверный выбор")
        return
    
    print("\n✅ Готово!")


if __name__ == "__main__":
    main()
