#!/bin/bash

# 🔍 Скрипт проверки статуса системы

echo "🔍 Проверка статуса RAG Chatbot системы..."
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для проверки сервиса
check_service() {
    local name=$1
    local url=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC} - работает на $url"
    else
        echo -e "${RED}❌ $name${NC} - недоступен на $url"
    fi
}

# Проверка сервисов
check_service "FastAPI сервер" "http://localhost:8000/docs"
check_service "Express сервер" "http://localhost:5000/api/health"
check_service "Vite dev сервер" "http://localhost:3001"

echo ""
echo "📁 Проверка директорий:"

# Проверка директорий
directories=("model_files" "data_files" "uploads")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $dir${NC} - существует"
    else
        echo -e "${RED}❌ $dir${NC} - не существует"
    fi
done

echo ""
echo "📊 Статистика файлов:"

# Статистика файлов
if [ -d "data_files" ]; then
    csv_count=$(find data_files -name "*.csv" | wc -l)
    echo -e "${BLUE}📄 CSV файлов: $csv_count${NC}"
fi

if [ -d "model_files" ]; then
    model_count=$(find model_files -type f | wc -l)
    echo -e "${BLUE}📄 Файлов модели: $model_count${NC}"
fi

echo ""
echo "🔧 Полезные команды:"
echo "   • Запуск системы: ./start.sh"
echo "   • Остановка: Ctrl+C"
echo "   • Логи: смотрите в терминалах"
