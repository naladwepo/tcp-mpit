#!/usr/bin/env python3
"""
ШПАРГАЛКА: Тестирование API

Быстрый запуск:
    python test_api_simple.py

Или:
    ./run_api_tests.sh
"""

# Перед запуском убедитесь что:
# 1. API запущен: uvicorn src.api.main:app --reload
# 2. Установлен requests: pip install requests

# Файлы для тестирования:
QUERY_FILES = [
    "query_1_simple.json",    # Крышка 200 мм
    "query_2_simple.json",    # Гайка М6
    "query_4_medium.json",    # Короб 100x100 мм
    "query_5_medium.json",    # Крышка углового лотка
    "query_8_complex.json"    # Комплект для монтажа
]

# API URL (измените если нужно)
API_BASE_URL = "http://localhost:8000"

# Результаты сохраняются в:
# - api_test_results.json

# Документация:
# - QUICKSTART_API_TESTS.md - быстрый старт
# - TEST_API_README.md - полная документация  
# - API_TESTING_SUMMARY.md - резюме тестирования
