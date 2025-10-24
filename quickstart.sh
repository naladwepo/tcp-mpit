#!/bin/bash

# Скрипт быстрого старта RAG-системы

echo "=================================="
echo "RAG-система поиска комплектующих"
echo "=================================="
echo ""

# Проверка Python
echo "[1/3] Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version найден"

# Установка зависимостей
echo ""
echo "[2/3] Установка зависимостей..."
echo "Это может занять несколько минут..."

pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Зависимости установлены"
else
    echo "⚠ Возникли проблемы при установке"
    echo "Попробуйте вручную: pip install -r requirements.txt"
fi

# Запуск системы
echo ""
echo "[3/3] Запуск системы..."
echo ""
echo "=================================="
echo "Система готова!"
echo "=================================="
echo ""
echo "Примеры использования:"
echo ""
echo "1. Одиночный запрос:"
echo "   python main.py \"Гайка М6\""
echo ""
echo "2. Интерактивный режим:"
echo "   python main.py --interactive"
echo ""
echo "3. Тестирование:"
echo "   python test_queries.py"
echo ""
echo "4. Без LLM (быстрее):"
echo "   python main.py \"Короб 100x100\" --no-llm"
echo ""
echo "=================================="
