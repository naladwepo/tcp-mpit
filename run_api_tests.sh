#!/bin/bash
# Быстрый запуск тестирования API

echo "=========================================="
echo "  ТЕСТИРОВАНИЕ API ПОИСКА КОМПЛЕКТУЮЩИХ"
echo "=========================================="
echo ""

# Проверяем, запущен ли API
echo "Проверка доступности API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API доступен"
else
    echo "✗ API не запущен!"
    echo ""
    echo "Запустите API в отдельном терминале:"
    echo "  uvicorn src.api.main:app --reload"
    echo ""
    exit 1
fi

echo ""
echo "Запуск тестов..."
echo ""

# Запускаем тесты
python3 test_api_simple.py

echo ""
echo "Готово!"
