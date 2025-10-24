# 🚀 Запуск системы одной командой

## ✅ Готово! Теперь можно запустить всю систему одной командой:

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
npm run start:all
```

## 🎯 Что запускается автоматически:

1. **Проверка зависимостей** (Node.js, Python)
2. **Установка пакетов** (npm install + pip install)
3. **Создание директорий** (model_files, data_files, uploads)
4. **Запуск всех сервисов**:
   - FastAPI сервер (порт 8000)
   - Express сервер (порт 5000)
   - Vite dev сервер (порт 3001)

## 🌐 После запуска доступны:

- **Веб-интерфейс**: http://localhost:3001
- **Админ-панель**: http://localhost:3001/admin
- **FastAPI API**: http://localhost:8000
- **FastAPI Docs**: http://localhost:8000/docs

## 🛑 Остановка:

- **Linux/macOS**: `Ctrl+C`
- **Windows**: Закройте окна терминалов

## 🔧 Проверка статуса:

```bash
./check_status.sh
```

## 🎉 Готово к использованию!

Система полностью интегрирована и готова к работе с RAG-моделью!
