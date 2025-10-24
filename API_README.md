# RAG API для поиска комплектующих

## Запуск API

### 1. Установка зависимостей

```bash
pip install fastapi uvicorn pydantic
```

### 2. Запуск сервера

```bash
# Вариант 1: через скрипт
python run_api.py

# Вариант 2: напрямую через uvicorn
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Открыть в браузере

- **Веб-интерфейс**: http://localhost:8000
- **API документация**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## API Endpoints

### POST /search

Основной эндпоинт для поиска комплектующих.

**Request Body:**
```json
{
  "query": "Гайка М6",
  "top_k": 10,
  "use_decomposition": true,
  "complexity": "simple"
}
```

**Response:**
```json
{
  "found_items": [
    {
      "name": "Гайка М6,оцинкованная",
      "cost": "13 688 руб."
    }
  ],
  "items_count": 10,
  "total_cost": "348 684 руб.",
  "query": "Гайка М6"
}
```

**Пример с curl:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Короб 200x200",
    "top_k": 5,
    "use_decomposition": true
  }'
```

### GET /search

Упрощенный GET эндпоинт для быстрого тестирования.

**Параметры:**
- `q` (required): поисковый запрос
- `top_k` (optional): количество результатов (default: 10)
- `decompose` (optional): использовать декомпозицию (default: true)

**Примеры:**
```bash
# Простой запрос
curl "http://localhost:8000/search?q=Гайка%20М6"

# С параметрами
curl "http://localhost:8000/search?q=Крышка%20200&top_k=5&decompose=true"
```

### GET /health

Проверка состояния системы.

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "products_count": 98,
  "embedding_model": "intfloat/multilingual-e5-small",
  "llm_available": true
}
```

### GET /products/count

Получить количество товаров в базе.

**Response:**
```json
{
  "count": 98
}
```

### GET /products/categories

Получить список категорий товаров.

**Response:**
```json
{
  "categories": [
    "Винт с крестообразным шлицем",
    "Гайка",
    "Короб",
    "Крышка"
  ],
  "count": 4
}
```

## Примеры использования

### Python

```python
import requests

# Поиск
response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки",
        "top_k": 10,
        "use_decomposition": True
    }
)

data = response.json()
print(f"Найдено: {data['items_count']} товаров")
print(f"Общая стоимость: {data['total_cost']}")

for item in data['found_items']:
    print(f"- {item['name']}: {item['cost']}")
```

### JavaScript

```javascript
// Поиск
const response = await fetch('http://localhost:8000/search', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        query: 'Гайка М6',
        top_k: 10,
        use_decomposition: true
    })
});

const data = await response.json();
console.log('Найдено:', data.items_count);
console.log('Стоимость:', data.total_cost);
```

## Особенности

### Умный поиск (декомпозиция)

Когда включен параметр `use_decomposition`, система автоматически:
1. Разбивает сложные запросы на компоненты с помощью LLM (Qwen)
2. Ищет каждый компонент отдельно
3. Объединяет результаты

**Пример:**
```
Запрос: "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки"

Декомпозиция:
1. Короб 200x200
2. Крышка 200
3. Винт М6
4. Гайка М6

Результат: товары по всем 4 компонентам
```

### Модели

- **Векторный поиск**: `intfloat/multilingual-e5-small` (384 измерения)
- **LLM препроцессинг**: `Qwen3-4B-Instruct-2507`
- **Индекс**: FAISS (Inner Product для косинусного сходства)

## Производительность

- Загрузка моделей: ~25 секунд (при первом запуске)
- Поиск (простой запрос): ~0.1-0.3 секунды
- Поиск (сложный с декомпозицией): ~0.5-1.5 секунды
- Память: ~2-3 GB (с LLM)

## Troubleshooting

### Ошибка "Система не инициализирована"

Подождите 20-30 секунд после запуска - модели загружаются в фоне.

### LLM не загружается

Проверьте наличие модели в `./Qwen/Qwen3-4B-Instruct-2507/`. Если LLM не критичен, система использует простой парсер.

### CORS ошибки

API настроен с `allow_origins=["*"]`, но при необходимости можно ограничить в `src/api/main.py`.

## Разработка

### Добавление новых эндпоинтов

Редактируйте `src/api/main.py`:

```python
@app.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello!"}
```

### Изменение моделей

В `src/api/main.py` в функции `startup_event()`:

```python
embedding_model = "your-model-name"
index_dir = "data/your_index"
```

## Развертывание

### Production с Gunicorn

```bash
pip install gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Лицензия

MIT
