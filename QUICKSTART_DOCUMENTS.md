# 🚀 Быстрый старт: Генерация ТКП

## Установка

```bash
pip install python-docx
```

## Запуск API

```bash
uvicorn src.api.main:app --reload
```

## Генерация документа

### Через curl (Word)

```bash
curl -X POST "http://localhost:8000/generate/word" \
  -H "Content-Type: application/json" \
  -d '{"query": "Короб 200x200 и крышка", "use_llm": true}' \
  -o tkp.docx
```

### Через Python

```python
import requests

response = requests.post(
    "http://localhost:8000/generate/word",
    json={"query": "Короб 200x200 и крышка", "use_llm": True}
)

with open("tkp.docx", "wb") as f:
    f.write(response.content)
```

### Тестовый скрипт

```bash
python test_document_generation.py
```

## API эндпоинты

- `POST /generate/word` - генерация Word
- `POST /generate/pdf` - генерация PDF (требует LibreOffice)
- `POST /generate/both` - оба формата
- `GET /download/{filename}` - скачать файл

## Документы сохраняются в

```
generated_documents/
```

## Полная документация

См. [DOCUMENT_GENERATION.md](DOCUMENT_GENERATION.md)
