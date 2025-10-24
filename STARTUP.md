# Инструкции по запуску RAG Chatbot

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
npm install
```

### 2. Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
PORT=5000
RAG_API_URL=http://localhost:8000/api/rag
RAG_API_KEY=your_api_key_here
```

### 3. Запуск в режиме разработки

**Вариант 1: Запуск фронтенда и бэкенда отдельно**
```bash
# Терминал 1 - Бэкенд
npm start

# Терминал 2 - Фронтенд
npm run dev
```

**Вариант 2: Только фронтенд (для разработки UI)**
```bash
npm run dev
```

### 4. Сборка для продакшена
```bash
npm run build
npm start
```

## 🔧 Интеграция с RAG API

### Шаг 1: Выберите метод интеграции
Откройте файл `server.js` и замените функцию `simulateRAGResponse` на одну из функций из `rag-integrations.js`:

```javascript
// Импортируйте нужную функцию
const { callCustomRAG } = require('./rag-integrations')

// Замените simulateRAGResponse на вашу функцию
const response = await callCustomRAG(message)
```

### Шаг 2: Настройте переменные окружения
Добавьте в `.env` файл необходимые ключи API и URL.

### Шаг 3: Протестируйте интеграцию
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Привет, как дела?"}'
```

## 📱 Доступ к приложению

- **Фронтенд:** http://localhost:3000
- **Бэкенд API:** http://localhost:5000
- **Health Check:** http://localhost:5000/api/health

## 🛠 Полезные команды

```bash
# Проверка статуса API
curl http://localhost:5000/api/health

# Тест чата
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Тестовое сообщение"}'

# Просмотр логов
npm run dev 2>&1 | tee logs/app.log
```

## 🔍 Отладка

### Проблемы с CORS
Если возникают ошибки CORS, проверьте настройки в `server.js`:
```javascript
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000'
}))
```

### Проблемы с API
1. Проверьте правильность URL в переменных окружения
2. Убедитесь, что API ключи корректны
3. Проверьте логи сервера на наличие ошибок

### Проблемы с фронтендом
1. Убедитесь, что бэкенд запущен на порту 5000
2. Проверьте прокси настройки в `vite.config.js`
3. Очистите кэш браузера

## 📊 Мониторинг

Приложение включает:
- Health check endpoint для мониторинга
- Логирование ошибок
- Счетчик сообщений в интерфейсе
- Индикатор состояния подключения

## 🚀 Деплой

### Docker (рекомендуется)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 5000
CMD ["npm", "start"]
```

### PM2
```bash
npm install -g pm2
pm2 start server.js --name "rag-chatbot"
pm2 startup
pm2 save
```

Интерфейс готов к использованию! 🎉

