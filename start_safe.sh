#!/bin/bash

# 🚀 Улучшенный скрипт запуска с проверкой портов

echo "🚀 Запуск RAG Chatbot системы..."
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Функция очистки портов
clear_ports() {
    print_status "Очистка портов 3000, 3001, 5550, 8000..."
    for port in 3000 3001 5550 8000; do
        pid=$(lsof -ti :$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            print_warning "Порт $port занят процессом $pid, освобождаю..."
            kill -9 $pid 2>/dev/null
            sleep 0.5
        fi
    done
    print_success "Все порты очищены"
}

# Функция завершения
cleanup() {
    print_status "Завершение всех процессов..."
    jobs -p | xargs kill 2>/dev/null
    clear_ports
    exit 0
}

trap cleanup SIGINT SIGTERM

# Очистка портов перед запуском
clear_ports
echo ""

# Проверка зависимостей
print_status "Проверка зависимостей..."

if ! command -v node &> /dev/null; then
    print_error "Node.js не установлен"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python3 не установлен"
    exit 1
fi

print_success "Зависимости найдены"
echo ""

# Создание директорий
print_status "Создание директорий..."
mkdir -p model_files data_files uploads generated_documents
print_success "Директории созданы"
echo ""

# Запуск FastAPI
print_status "Запуск FastAPI сервера на порту 8000..."
if [ -f "src/api/main.py" ]; then
    python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload > fastapi.log 2>&1 &
    FASTAPI_PID=$!
    print_success "FastAPI запущен (PID: $FASTAPI_PID)"
    sleep 3
    
    # Проверка
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ FastAPI работает на http://localhost:8000"
    else
        print_warning "⚠️  FastAPI недоступен, проверьте fastapi.log"
    fi
else
    print_error "src/api/main.py не найден"
fi
echo ""

# Запуск Express
print_status "Запуск Express сервера на порту 5550..."
if [ -f "server.js" ]; then
    node server.js > express.log 2>&1 &
    EXPRESS_PID=$!
    print_success "Express запущен (PID: $EXPRESS_PID)"
    sleep 2
    
    # Проверка
    if curl -s http://localhost:5550/api/health > /dev/null 2>&1; then
        print_success "✅ Express работает на http://localhost:5550"
    else
        print_warning "⚠️  Express недоступен, проверьте express.log"
    fi
else
    print_error "server.js не найден"
fi
echo ""

# Запуск Vite
print_status "Запуск Vite dev сервера на порту 3001..."
if [ -f "package.json" ]; then
    npm run dev > vite.log 2>&1 &
    VITE_PID=$!
    print_success "Vite запущен (PID: $VITE_PID)"
    sleep 3
    
    # Проверка
    if curl -s http://localhost:3001 > /dev/null 2>&1; then
        print_success "✅ Vite работает на http://localhost:3001"
    else
        print_warning "⚠️  Vite недоступен, проверьте vite.log"
    fi
else
    print_error "package.json не найден"
fi
echo ""

echo "════════════════════════════════════════════════════════════════════"
echo "🎉 Система запущена!"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "📱 Доступные сервисы:"
echo "   • Веб-интерфейс:    http://localhost:3001"
echo "   • FastAPI:          http://localhost:8000"
echo "   • FastAPI Docs:     http://localhost:8000/docs"
echo "   • Express API:      http://localhost:5550"
echo ""
echo "📝 Логи:"
echo "   • FastAPI:  tail -f fastapi.log"
echo "   • Express:  tail -f express.log"
echo "   • Vite:     tail -f vite.log"
echo ""
echo "🔧 Управление:"
echo "   • Нажмите Ctrl+C для остановки всех сервисов"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""

print_status "Система работает. Нажмите Ctrl+C для остановки..."

# Ожидание
wait
