@echo off
REM 🚀 Скрипт запуска всей системы одной командой для Windows
REM Автор: AI Assistant

echo 🚀 Запуск RAG Chatbot системы...

REM Проверка зависимостей
echo [INFO] Проверка зависимостей...

REM Проверка Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js не установлен. Установите Node.js: https://nodejs.org/
    pause
    exit /b 1
)

REM Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не установлен. Установите Python 3.8+
    pause
    exit /b 1
)

echo [SUCCESS] Все зависимости найдены

REM Установка Python зависимостей
echo [INFO] Установка Python зависимостей...
if exist requirements.txt (
    pip install -r requirements.txt
    echo [SUCCESS] Python зависимости установлены
) else (
    echo [WARNING] requirements.txt не найден, пропускаем установку Python зависимостей
)

REM Установка Node.js зависимостей
echo [INFO] Установка Node.js зависимостей...
if exist package.json (
    npm install
    echo [SUCCESS] Node.js зависимости установлены
) else (
    echo [ERROR] package.json не найден
    pause
    exit /b 1
)

REM Создание необходимых директорий
echo [INFO] Создание необходимых директорий...
if not exist model_files mkdir model_files
if not exist data_files mkdir data_files
if not exist uploads mkdir uploads
echo [SUCCESS] Директории созданы

REM Запуск FastAPI сервера
echo [INFO] Запуск FastAPI сервера на порту 8000...
if exist main.py (
    start "FastAPI Server" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    echo [SUCCESS] FastAPI сервер запущен
    timeout /t 3 /nobreak >nul
) else (
    echo [WARNING] main.py не найден, пропускаем запуск FastAPI
)

REM Запуск Express сервера
echo [INFO] Запуск Express сервера на порту 5000...
start "Express Server" cmd /k "node server.js"
echo [SUCCESS] Express сервер запущен
timeout /t 2 /nobreak >nul

REM Запуск Vite dev сервера
echo [INFO] Запуск Vite dev сервера на порту 3001...
start "Vite Dev Server" cmd /k "npm run dev"
echo [SUCCESS] Vite dev сервер запущен

REM Ожидание запуска всех сервисов
echo [INFO] Ожидание полного запуска всех сервисов...
timeout /t 5 /nobreak >nul

echo.
echo 🎉 Система запущена успешно!
echo.
echo 📱 Доступные сервисы:
echo    • Веб-интерфейс: http://localhost:3001
echo    • Админ-панель: http://localhost:3001/admin
echo    • FastAPI API: http://localhost:8000
echo    • FastAPI Docs: http://localhost:8000/docs
echo    • Express API: http://localhost:5000
echo.
echo 🔧 Управление:
echo    • Закройте окна терминалов для остановки сервисов
echo    • Логи будут отображаться в отдельных окнах терминалов
echo.
echo 📁 Файлы:
echo    • CSV файлы: .\data_files\
echo    • Файлы модели: .\model_files\
echo    • Временные файлы: .\uploads\
echo.

pause
