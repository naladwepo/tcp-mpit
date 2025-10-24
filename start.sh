#!/bin/bash

# 🚀 Скрипт запуска всей системы одной командой
# Автор: AI Assistant
# Дата: $(date)

echo "🚀 Запуск RAG Chatbot системы..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка зависимостей
print_status "Проверка зависимостей..."

# Проверка Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js не установлен. Установите Node.js: https://nodejs.org/"
    exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 не установлен. Установите Python 3.8+"
    exit 1
fi

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 не установлен. Установите pip3"
    exit 1
fi

print_success "Все зависимости найдены"

# Установка Python зависимостей
print_status "Установка Python зависимостей..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    print_success "Python зависимости установлены"
else
    print_warning "requirements.txt не найден, пропускаем установку Python зависимостей"
fi

# Установка Node.js зависимостей
print_status "Установка Node.js зависимостей..."
if [ -f "package.json" ]; then
    npm install
    print_success "Node.js зависимости установлены"
else
    print_error "package.json не найден"
    exit 1
fi

# Создание необходимых директорий
print_status "Создание необходимых директорий..."
mkdir -p model_files
mkdir -p data_files
mkdir -p uploads
print_success "Директории созданы"

# Функция для завершения всех процессов
cleanup() {
    print_status "Завершение всех процессов..."
    jobs -p | xargs -r kill
    exit 0
}

# Обработка сигналов для корректного завершения
trap cleanup SIGINT SIGTERM

# Запуск FastAPI сервера
print_status "Запуск FastAPI сервера на порту 8000..."
if [ -f "src/api/main.py" ]; then
    python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
    FASTAPI_PID=$!
    print_success "FastAPI сервер запущен (PID: $FASTAPI_PID)"
else
    print_warning "main.py не найден, пропускаем запуск FastAPI"
fi

# Ожидание запуска FastAPI
print_status "Ожидание запуска FastAPI..."
sleep 3

# Запуск Express сервера
print_status "Запуск Express сервера на порту 5000..."
node server.js &
EXPRESS_PID=$!
print_success "Express сервер запущен (PID: $EXPRESS_PID)"

# Ожидание запуска Express
print_status "Ожидание запуска Express..."
sleep 2

# Запуск Vite dev сервера
print_status "Запуск Vite dev сервера на порту 3001..."
npm run dev &
VITE_PID=$!
print_success "Vite dev сервер запущен (PID: $VITE_PID)"

# Ожидание запуска всех сервисов
print_status "Ожидание полного запуска всех сервисов..."
sleep 5

# Проверка статуса сервисов
print_status "Проверка статуса сервисов..."

# Проверка FastAPI
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    print_success "✅ FastAPI сервер работает на http://localhost:8000"
else
    print_warning "⚠️  FastAPI сервер недоступен на http://localhost:8000"
fi

# Проверка Express
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    print_success "✅ Express сервер работает на http://localhost:5000"
else
    print_warning "⚠️  Express сервер недоступен на http://localhost:5000"
fi

# Проверка Vite
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    print_success "✅ Vite dev сервер работает на http://localhost:3001"
else
    print_warning "⚠️  Vite dev сервер недоступен на http://localhost:3001"
fi

echo ""
echo "🎉 Система запущена успешно!"
echo ""
echo "📱 Доступные сервисы:"
echo "   • Веб-интерфейс: http://localhost:3001"
echo "   • Админ-панель: http://localhost:3001/admin"
echo "   • FastAPI API: http://localhost:8000"
echo "   • FastAPI Docs: http://localhost:8000/docs"
echo "   • Express API: http://localhost:5000"
echo ""
echo "🔧 Управление:"
echo "   • Нажмите Ctrl+C для остановки всех сервисов"
echo "   • Логи будут отображаться в этом терминале"
echo ""
echo "📁 Файлы:"
echo "   • CSV файлы: ./data_files/"
echo "   • Файлы модели: ./model_files/"
echo "   • Временные файлы: ./uploads/"
echo ""

# Ожидание завершения
print_status "Система работает. Нажмите Ctrl+C для остановки..."
wait
