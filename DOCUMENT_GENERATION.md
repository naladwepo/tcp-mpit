# 📄 Генерация Технико-Коммерческих Предложений (ТКП)

## Описание

API предоставляет функциональность для автоматической генерации профессиональных технико-коммерческих предложений в форматах Word (.docx) и PDF на основе результатов поиска комплектующих.

## 🎯 Возможности

- ✅ Генерация документов Word (.docx)
- ✅ Генерация документов PDF (опционально, требует дополнительные зависимости)
- ✅ Автоматическое форматирование таблиц и данных
- ✅ Фирменная шапка с данными компании
- ✅ Профессиональное оформление
- ✅ Расчет итоговой стоимости
- ✅ Условия поставки и подпись

## 📋 Структура документа

Каждый сгенерированный ТКП содержит:

1. **Шапка документа**
   - Заголовок "ТЕХНИКО-КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ"
   - Номер и дата документа
   - Данные компании (название, адрес, телефон, email, ИНН/КПП, ОГРН, директор)

2. **Таблица товаров**
   - Номер п/п
   - Наименование товара
   - Спецификация
   - Количество
   - Цена за единицу
   - Сумма
   - Итоговая строка с общей стоимостью

3. **Подвал**
   - Общая сумма (выделена)
   - Условия поставки
   - Подпись директора

## 🚀 API Эндпоинты

### 1. Генерация Word документа

```http
POST /generate/word
Content-Type: application/json

{
  "query": "Комплект для монтажа короба 200x200",
  "use_llm": true
}
```

**Ответ:** Word документ (.docx)

### 2. Генерация PDF документа

```http
POST /generate/pdf
Content-Type: application/json

{
  "query": "Комплект для монтажа короба 200x200",
  "use_llm": true
}
```

**Ответ:** PDF документ (или Word, если PDF недоступен)

### 3. Генерация обоих форматов

```http
POST /generate/both
Content-Type: application/json

{
  "query": "Комплект для монтажа короба 200x200",
  "use_llm": true
}
```

**Ответ:**
```json
{
  "message": "Документы успешно созданы",
  "files": {
    "word": {
      "filename": "TKP_20251024_123456.docx",
      "path": "generated_documents/TKP_20251024_123456.docx",
      "download_url": "/download/TKP_20251024_123456.docx"
    },
    "pdf": {
      "filename": "TKP_20251024_123456.pdf",
      "path": "generated_documents/TKP_20251024_123456.pdf",
      "download_url": "/download/TKP_20251024_123456.pdf"
    }
  }
}
```

### 4. Скачивание документа

```http
GET /download/{filename}
```

**Пример:**
```
GET /download/TKP_20251024_123456.docx
```

## 💻 Использование

### Через curl

**Word документ:**
```bash
curl -X POST "http://localhost:8000/generate/word" \
  -H "Content-Type: application/json" \
  -d '{"query": "Короб 200x200 и крышка", "use_llm": true}' \
  -o tkp.docx
```

**PDF документ:**
```bash
curl -X POST "http://localhost:8000/generate/pdf" \
  -H "Content-Type: application/json" \
  -d '{"query": "Короб 200x200 и крышка", "use_llm": true}' \
  -o tkp.pdf
```

**Оба формата:**
```bash
curl -X POST "http://localhost:8000/generate/both" \
  -H "Content-Type: application/json" \
  -d '{"query": "Короб 200x200 и крышка", "use_llm": true}'
```

### Через Python

```python
import requests

# Генерация Word
response = requests.post(
    "http://localhost:8000/generate/word",
    json={"query": "Короб 200x200 и крышка", "use_llm": True}
)

with open("tkp.docx", "wb") as f:
    f.write(response.content)

# Генерация PDF
response = requests.post(
    "http://localhost:8000/generate/pdf",
    json={"query": "Короб 200x200 и крышка", "use_llm": True}
)

with open("tkp.pdf", "wb") as f:
    f.write(response.content)

# Оба формата
response = requests.post(
    "http://localhost:8000/generate/both",
    json={"query": "Короб 200x200 и крышка", "use_llm": True}
)

result = response.json()
print(f"Word: {result['files']['word']['download_url']}")
print(f"PDF: {result['files']['pdf']['download_url']}")
```

### Тестовый скрипт

```bash
python test_document_generation.py
```

Скрипт предлагает интерактивный выбор запроса и формата документа.

## 📦 Установка зависимостей

### Базовая установка (Word)

```bash
pip install python-docx
```

### Полная установка (Word + PDF)

**Windows:**
```bash
pip install python-docx docx2pdf
```

**macOS/Linux:**
```bash
pip install python-docx
brew install --cask libreoffice  # для macOS
# или
sudo apt-get install libreoffice  # для Linux

pip install docx2pdf
```

Или через requirements.txt:
```bash
pip install -r requirements.txt
```

## ⚙️ Конфигурация

### Данные компании

Данные компании настраиваются в файле `src/document_generator.py`:

```python
COMPANY_INFO = {
    "name": "ООО «СтройТехКомплект»",
    "address": "123456, г. Москва, ул. Промышленная, д. 10, офис 305",
    "phone": "+7 (495) 123-45-67",
    "email": "info@stroytechcomplex.ru",
    "inn": "7701234567",
    "kpp": "770101001",
    "ogrn": "1127746123456",
    "director": "Иванов Иван Иванович"
}
```

### Условия поставки

Условия также можно настроить в `_add_footer()`:

```python
conditions = [
    "Срок поставки: 10-14 рабочих дней с момента оплаты",
    "Условия оплаты: 100% предоплата по безналичному расчету",
    "Гарантия: 12 месяцев от производителя",
    "Доставка: по согласованию (стоимость рассчитывается отдельно)",
    "Цены действительны в течение 14 календарных дней"
]
```

### Директория для документов

По умолчанию документы сохраняются в `generated_documents/`. Изменить можно при инициализации:

```python
document_generator = DocumentGenerator(output_dir="custom_path")
```

## 📊 Формат таблицы

| № | Наименование товара | Спецификация | Кол-во | Цена за ед. | Сумма |
|---|---------------------|--------------|--------|-------------|-------|
| 1 | Короб 200x200 мм... | 200x200 мм   | 2      | 88,498.00 ₽ | 176,996.00 ₽ |
| 2 | Крышка 200 мм...    | 200 мм       | 2      | 45,131.00 ₽ | 90,262.00 ₽ |
| **ИТОГО:** |  |  |  |  | **267,258.00 ₽** |

## 🎨 Стилизация

Документ использует:
- **Шрифт:** Calibri (по умолчанию в Word)
- **Размеры:**
  - Заголовки: 14-16pt
  - Основной текст: 10-11pt
  - Таблица: 9-10pt
- **Цвета:**
  - Заголовок таблицы: синий (#4472C4)
  - Итоговая строка: серый (#E7E6E6)
  - Границы: черный

## ⚠️ Важные замечания

### PDF генерация

1. **Windows:** Работает через `docx2pdf` напрямую
2. **macOS/Linux:** Требует установки LibreOffice
3. **Альтернатива:** Если PDF недоступен, возвращается Word документ

### Производительность

- Генерация Word: ~1-2 секунды
- Генерация PDF: ~5-10 секунд (зависит от LibreOffice)
- Поиск товаров: 10-40 секунд (зависит от запроса)

**Общее время:** 15-50 секунд на полный цикл

### Ограничения

- Максимальный размер файла: не ограничен
- Одновременные запросы: поддерживаются
- Хранение файлов: файлы не удаляются автоматически

## 🔧 Решение проблем

### PDF не генерируется

```
⚠️ Библиотека docx2pdf не установлена
```

**Решение:**
```bash
pip install docx2pdf
# На macOS/Linux также нужен LibreOffice
brew install --cask libreoffice
```

### Ошибка импорта docx

```
ModuleNotFoundError: No module named 'docx'
```

**Решение:**
```bash
pip install python-docx
```

### Файлы не сохраняются

**Проверьте:**
1. Права на запись в `generated_documents/`
2. Наличие директории (создается автоматически)
3. Свободное место на диске

## 📚 Дополнительные ресурсы

- [python-docx документация](https://python-docx.readthedocs.io/)
- [docx2pdf GitHub](https://github.com/AlJohri/docx2pdf)
- [API документация](http://localhost:8000/docs)

## 🎯 Примеры использования

### Простой запрос

```bash
curl -X POST "http://localhost:8000/generate/word" \
  -H "Content-Type: application/json" \
  -d '{"query": "Гайка М6", "use_llm": true}' \
  -o gajka.docx
```

### Сложный комплект

```bash
curl -X POST "http://localhost:8000/generate/word" \
  -H "Content-Type: application/json" \
  -d '{"query": "Комплект: короб 200x200, крышка, 10 винтов М6, 10 гаек", "use_llm": true}' \
  -o komplekt.docx
```

### Скачивание существующего документа

```bash
curl "http://localhost:8000/download/TKP_20251024_123456.docx" -o downloaded.docx
```

## 📄 Формат имени файла

Автоматически генерируемое имя файла:
```
TKP_YYYYMMDD_HHMMSS.docx
TKP_YYYYMMDD_HHMMSS.pdf
```

Пример: `TKP_20251024_143522.docx`

## ✅ Готово к использованию!

API готов генерировать профессиональные ТКП документы автоматически! 🎉
