# 🌐 API ДОКУМЕНТАЦИЯ (Новая Архитектура)

## Обзор

FastAPI приложение для поиска комплектующих с использованием **новой архитектуры**:
```
LLM парсер → Векторный поиск → Расчет стоимости → Ответ
```

## Запуск API

```bash
# Запуск с перезагрузкой
uvicorn src.api.main:app --reload

# Запуск на определенном порту
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

API доступен на: `http://localhost:8000`

## Эндпоинты

### 1. Главная страница
```
GET /
```
Возвращает HTML интерфейс для работы с API

### 2. API информация
```
GET /api
```

**Ответ:**
```json
{
  "message": "RAG Поиск Комплектующих API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

### 3. Health Check
```
GET /health
```

**Ответ:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "products_count": 98,
  "embedding_model": "intfloat/multilingual-e5-small",
  "llm_available": true
}
```

**Параметры:**
- `status`: "healthy" или "unhealthy"
- `models_loaded`: загружены ли модели
- `products_count`: количество товаров в БД
- `embedding_model`: модель для эмбеддингов
- `llm_available`: доступен ли LLM парсер

### 4. Поиск (POST)
```
POST /search
```

**Тело запроса:**
```json
{
  "query": "Комплект для монтажа: короб 200x200, крышка, 4 винта М6",
  "top_k": 3,
  "use_llm": true
}
```

**Параметры:**
- `query` (string, required): Поисковый запрос
- `top_k` (int, optional): Количество результатов на каждый товар (1-10, default: 3)
- `use_llm` (bool, optional): Использовать LLM парсер (default: true)

**Ответ:**
```json
{
  "query_id": null,
  "original_query": "Комплект для монтажа: короб 200x200, крышка, 4 винта М6",
  "items": [
    {
      "requested_item": "Короб 200x200",
      "quantity": 1,
      "found_product": {
        "id": 3,
        "name": "Короб 200x200 мм, L=2000 мм, горячее цинкование...",
        "cost": 88498.0,
        "category": "Короб"
      },
      "relevance_score": 0.9847,
      "unit_price": 88498.0,
      "total_price": 88498.0,
      "specifications": "200x200 мм",
      "alternatives": [...]
    },
    {
      "requested_item": "Крышка 200",
      "quantity": 1,
      "found_product": {...},
      "unit_price": 45131.0,
      "total_price": 45131.0,
      ...
    },
    {
      "requested_item": "Винт М6",
      "quantity": 4,
      "found_product": {...},
      "unit_price": 19047.0,
      "total_price": 76188.0,
      ...
    }
  ],
  "total_items": 3,
  "found_items": 3,
  "total_cost": 209817.0,
  "currency": "RUB"
}
```

### 5. Поиск (GET)
```
GET /search?q=короб+200x200&top_k=3&use_llm=true
```

**Параметры:**
- `q` (string, required): Поисковый запрос
- `top_k` (int, optional): Количество результатов на товар (default: 3)
- `use_llm` (bool, optional): Использовать LLM (default: true)

**Пример:**
```
GET /search?q=Комплект:%20короб%20200x200,%20крышка,%20винты
```

### 6. Количество товаров
```
GET /products/count
```

**Ответ:**
```json
{
  "count": 98
}
```

### 7. Категории товаров
```
GET /products/categories
```

**Ответ:**
```json
{
  "categories": [
    "Болт",
    "Винт",
    "Гайка",
    "Короб",
    "Крышка",
    ...
  ],
  "count": 25
}
```

## Примеры использования

### cURL

**Простой запрос:**
```bash
curl -X GET "http://localhost:8000/search?q=Гайка%20М6&top_k=3"
```

**Комплект:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Комплект: короб 200x200, крышка, 4 винта М6, 4 гайки М6",
    "top_k": 3,
    "use_llm": true
  }'
```

### Python (requests)

```python
import requests

# Простой запрос
response = requests.get(
    "http://localhost:8000/search",
    params={"q": "Короб 200x200", "top_k": 3}
)
result = response.json()
print(f"Найдено: {result['found_items']} товаров")
print(f"Итого: {result['total_cost']:,} руб.")

# Комплект (POST)
response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "Комплект для монтажа: короб, крышка, винты",
        "top_k": 3,
        "use_llm": True
    }
)
result = response.json()

for item in result['items']:
    print(f"{item['requested_item']}: {item['quantity']} шт. × {item['unit_price']:,} = {item['total_price']:,} руб.")
```

### JavaScript (fetch)

```javascript
// GET запрос
fetch('http://localhost:8000/search?q=Короб%20200x200&top_k=3')
  .then(response => response.json())
  .then(data => {
    console.log('Найдено:', data.found_items, 'товаров');
    console.log('Стоимость:', data.total_cost, data.currency);
  });

// POST запрос
fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Комплект: короб 200x200, крышка, винты',
    top_k: 3,
    use_llm: true
  })
})
  .then(response => response.json())
  .then(data => {
    data.items.forEach(item => {
      console.log(`${item.requested_item}: ${item.quantity} шт.`);
      console.log(`  → ${item.found_product?.name}`);
      console.log(`  💰 ${item.total_price} руб.`);
    });
  });
```

## Особенности новой архитектуры

### 1. LLM парсинг на входе
- LLM **сразу** разбирает запрос на список товаров + количество
- Автоопределение устройства (CUDA > MPS > CPU)
- Точность определения количества: ~95%

### 2. Детализированный ответ
Каждый товар в ответе содержит:
- `requested_item`: что запросил пользователь
- `quantity`: количество (определено LLM)
- `found_product`: найденный товар с полной информацией
- `unit_price`: цена за единицу
- `total_price`: итоговая стоимость (quantity × unit_price)
- `alternatives`: альтернативные товары

### 3. Автоматический расчет стоимости
API автоматически считает:
- Стоимость каждой позиции (количество × цена)
- Общую стоимость всего комплекта

## Интерактивная документация

Swagger UI доступен на: **http://localhost:8000/docs**

![Swagger UI](https://fastapi.tiangolo.com/img/index/index-01-swagger-ui-simple.png)

Здесь можно:
- 📖 Изучить все эндпоинты
- 🧪 Протестировать API прямо в браузере
- 📋 Посмотреть примеры запросов/ответов

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Неверные параметры запроса |
| 500 | Ошибка при обработке запроса |
| 503 | Система не инициализирована |

## Производительность

### Время ответа (среднее)

| Запрос | LLM (GPU) | LLM (CPU) | Fallback |
|--------|-----------|-----------|----------|
| Простой (1 товар) | ~5s | ~60s | ~0.5s |
| Средний (2-3 товара) | ~8s | ~80s | ~1s |
| Сложный (4+ товара) | ~12s | ~120s | ~2s |

### Рекомендации
- ✅ Для продакшена: GPU (CUDA/MPS)
- ⚡ Для быстрых запросов: `use_llm=false` (fallback)
- 🔧 Для разработки: CPU (медленно, но работает)

## CORS

API поддерживает CORS для всех источников (`allow_origins=["*"]`).

Для продакшена рекомендуется ограничить:
```python
allow_origins=["https://your-frontend.com"]
```

## Мониторинг

Проверяйте здоровье системы через `/health`:
```bash
curl http://localhost:8000/health
```

Если `llm_available=false` → LLM не загружена (возможно, недостаточно памяти)

## Миграция со старого API

### Было (старый формат)
```json
{
  "query": "Гайка М6",
  "top_k": 10,
  "use_decomposition": true,
  "complexity": "simple"
}
```

### Стало (новый формат)
```json
{
  "query": "Комплект: короб 200x200, крышка, 4 винта М6",
  "top_k": 3,
  "use_llm": true
}
```

### Изменения в ответе
- ✅ Добавлено `quantity` для каждого товара
- ✅ Добавлено `total_price` = unit_price × quantity
- ✅ Детальная информация о каждом товаре
- ✅ Альтернативные товары
- ✅ Общая стоимость в числовом формате (float)
