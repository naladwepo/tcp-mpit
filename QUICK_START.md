# 🚀 Быстрый запуск системы

## Одна команда для запуска всей системы!

### 🐧 Linux/macOS:
```bash
./start.sh
```

### 🪟 Windows:
```cmd
start.bat
```

### 📦 Или через npm:
```bash
# Linux/macOS
npm run start:all

# Windows
npm run start:windows
```

## 🎯 Что происходит при запуске:

1. **Проверка зависимостей** - Node.js, Python, pip
2. **Установка зависимостей** - npm install + pip install
3. **Создание директорий** - model_files, data_files, uploads
4. **Запуск сервисов**:
   - FastAPI сервер (порт 8000)
   - Express сервер (порт 5000)
   - Vite dev сервер (порт 3001)

## 🌐 Доступные сервисы:

- **Веб-интерфейс**: http://localhost:3001
- **Админ-панель**: http://localhost:3001/admin
- **FastAPI API**: http://localhost:8000
- **FastAPI Docs**: http://localhost:8000/docs
- **Express API**: http://localhost:5000

## 🛑 Остановка системы:

- **Linux/macOS**: Нажмите `Ctrl+C` в терминале
- **Windows**: Закройте окна терминалов

## 📁 Структура файлов:

- `model_files/` - файлы модели
- `data_files/` - CSV файлы с данными
- `uploads/` - временные файлы

## 🔧 Ручной запуск (если скрипты не работают):

### Терминал 1 - FastAPI:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Терминал 2 - Express:
```bash
node server.js
```

### Терминал 3 - Vite:
```bash
npm run dev
```

## ❗ Требования:

- Node.js 16+
- Python 3.8+
- pip3

## 🎉 Готово!

После запуска откройте http://localhost:3001 и наслаждайтесь работой с RAG Chatbot!
