# 🔧 Исправление ошибки 500 в FastAPI

## ❌ Проблема
```
INFO: 127.0.0.1:59226 - "POST /search HTTP/1.1" 500 Internal Server Error
Ошибка FastAPI: Error: FastAPI error: 500
```

## 🔍 Диагностика
Ошибка была в том, что в модели `SearchRequest` отсутствовало поле `complexity`, но код пытался его использовать.

## ✅ Решение

### 1. Добавлено поле `complexity` в модель `SearchRequest`
```python
class SearchRequest(BaseModel):
    """Запрос на поиск"""
    query: str = Field(..., description="Поисковый запрос", example="Гайка М6")
    top_k: int = Field(10, description="Количество результатов", ge=1, le=50)
    use_decomposition: bool = Field(True, description="Использовать декомпозицию для сложных запросов")
    complexity: Optional[str] = Field(None, description="Сложность запроса (simple/medium/complex)")
```

### 2. Проверка работы API
- ✅ FastAPI endpoint `/search` работает корректно
- ✅ Express endpoint `/api/chat` работает корректно
- ✅ Интеграция между сервисами работает

## 🧪 Тестирование

### Тест FastAPI напрямую:
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"гайка","top_k":5,"use_decomposition":true}'
```

### Тест через Express:
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"гайка М6"}'
```

## 🎯 Результат

Теперь система работает корректно:
- ✅ **FastAPI** - поиск работает без ошибок
- ✅ **Express** - интеграция с FastAPI работает
- ✅ **Веб-интерфейс** - чат работает корректно
- ✅ **CSV загрузка** - система готова к обновлению данных

## 📁 Измененные файлы:
- `src/api/main.py` - добавлено поле `complexity` в `SearchRequest`

Система готова к использованию! 🎉
