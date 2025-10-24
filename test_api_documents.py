#!/usr/bin/env python3
"""
Тест генерации документов через API
Убедитесь, что API запущен: uvicorn src.api.main:app --reload
"""

import requests
import json
from pathlib import Path

API_URL = "http://localhost:8000"

def test_generate_both():
    """Тест генерации обоих форматов через API"""
    
    print("=" * 70)
    print("  ТЕСТ: Генерация DOCX и PDF через API")
    print("=" * 70)
    print()
    
    # Проверяем доступность API
    print("🔍 Проверка API...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API доступен")
            health = response.json()
            print(f"  Статус: {health.get('status')}")
            print(f"  LLM: {health.get('llm_available')}")
        else:
            print("✗ API недоступен")
            return
    except:
        print("✗ API не запущен!")
        print("  Запустите: uvicorn src.api.main:app --reload")
        return
    
    print()
    
    # Тестовый запрос
    query = "Короб 200x200 и крышка"
    
    print(f"📝 Запрос: {query}")
    print()
    
    # Генерируем оба формата
    print("🔄 Генерация документов...")
    
    try:
        response = requests.post(
            f"{API_URL}/generate/both",
            json={"query": query, "use_llm": True},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Документы созданы!")
            print()
            
            print("📄 Word документ:")
            print(f"   Имя: {result['files']['word']['filename']}")
            print(f"   URL: {API_URL}{result['files']['word']['download_url']}")
            print()
            
            print("📕 PDF документ:")
            print(f"   Имя: {result['files']['pdf']['filename']}")
            print(f"   URL: {API_URL}{result['files']['pdf']['download_url']}")
            print()
            
            # Скачиваем файлы
            print("⬇️  Скачивание файлов...")
            
            # Word
            word_url = f"{API_URL}{result['files']['word']['download_url']}"
            word_response = requests.get(word_url)
            word_filename = f"downloaded_{result['files']['word']['filename']}"
            
            with open(word_filename, 'wb') as f:
                f.write(word_response.content)
            print(f"   ✓ Word сохранен: {word_filename}")
            
            # PDF
            pdf_url = f"{API_URL}{result['files']['pdf']['download_url']}"
            pdf_response = requests.get(pdf_url)
            pdf_filename = f"downloaded_{result['files']['pdf']['filename']}"
            
            with open(pdf_filename, 'wb') as f:
                f.write(pdf_response.content)
            print(f"   ✓ PDF сохранен: {pdf_filename}")
            
            print()
            print("=" * 70)
            print("✅ Тест успешно завершен!")
            print()
            print("💡 Откройте файлы:")
            print(f"   open {word_filename}")
            print(f"   open {pdf_filename}")
            print()
            
        else:
            print(f"✗ Ошибка: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_generate_both()
