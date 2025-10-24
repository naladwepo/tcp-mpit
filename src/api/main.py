"""
FastAPI приложение для RAG-поиска комплектующих
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from pathlib import Path

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine
from src.hybrid_processor import HybridQueryProcessor
from src.document_generator import DocumentGenerator

# Инициализация FastAPI
app = FastAPI(
    title="RAG Поиск Комплектующих",
    description="API для поиска строительных комплектующих с использованием RAG (Retrieval-Augmented Generation)",
    version="1.0.0"
)

# Статические файлы
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные для моделей
search_engine: Optional[VectorSearchEngine] = None
processor: Optional[HybridQueryProcessor] = None
products_loaded: bool = False
document_generator: Optional[DocumentGenerator] = None


# Pydantic модели
class SearchRequest(BaseModel):
    """Запрос на поиск"""
    query: str = Field(..., description="Поисковый запрос", example="Комплект: короб 200x200, крышка, 4 винта М6")
    use_llm: bool = Field(True, description="Использовать LLM для парсинга запроса")


class ProductInfo(BaseModel):
    """Информация о найденном товаре"""
    id: int
    name: str
    cost: float
    category: str


class SearchResultItem(BaseModel):
    """Элемент результата поиска"""
    requested_item: str
    quantity: int
    found_product: Optional[ProductInfo]
    relevance_score: float
    unit_price: float
    total_price: float
    specifications: str
    alternatives: List[Dict[str, Any]] = []


class SearchResponse(BaseModel):
    """Ответ на поиск"""
    query_id: Optional[int]
    original_query: str
    items: List[SearchResultItem]
    total_items: int
    found_items: int
    total_cost: float
    currency: str


class HealthResponse(BaseModel):
    """Статус здоровья системы"""
    status: str
    models_loaded: bool
    products_count: int
    embedding_model: str
    llm_available: bool


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    detail: str
    error_type: str


@app.on_event("startup")
async def startup_event():
    """Инициализация при старте приложения"""
    global search_engine, processor, products_loaded, document_generator
    
    print("=" * 70)
    print("🚀 Запуск RAG API...")
    print("=" * 70)
    
    try:
        # Загружаем данные
        print("📦 Загрузка данных о товарах...")
        data_loader = DataLoader()
        products_df = data_loader.get_products()
        print(f"✓ Загружено продуктов: {len(products_df)}")
        
        # Инициализируем векторный поиск
        print("🔍 Инициализация векторного поиска...")
        embedding_model = "intfloat/multilingual-e5-small"
        index_dir = "data/index_e5"
        
        search_engine = VectorSearchEngine(
            model_name=embedding_model,
            index_dir=index_dir
        )
        
        # Загружаем или создаем индекс
        if not search_engine.load_index():
            print("🔨 Создание индекса (это может занять некоторое время)...")
            search_engine.build_index(products_df)
            print("✓ Индекс создан и сохранен")
        else:
            print("✓ Индекс загружен из кэша")
        
        # Создаем гибридный процессор с новой архитектурой
        print("🤖 Инициализация гибридного процессора (новая архитектура)...")
        processor = HybridQueryProcessor(
            search_engine=search_engine,
            use_llm_parser=True,  # LLM парсер на входе с автоопределением CUDA/MPS/CPU
            use_fallback_enhancement=True
        )
        
        # Инициализируем генератор документов
        print("📄 Инициализация генератора документов...")
        document_generator = DocumentGenerator(output_dir="generated_documents")
        
        products_loaded = True
        print("=" * 70)
        print("✅ RAG API готов к работе!")
        print(f"📊 Модель эмбеддингов: {embedding_model}")
        print(f"🗂️  Индекс: {index_dir}")
        print(f"📦 Товаров в базе: {len(products_df)}")
        print(f"📄 Документы: generated_documents/")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        import traceback
        traceback.print_exc()
        products_loaded = False


@app.get("/", response_class=HTMLResponse)
async def root():
    """Корневой эндпоинт - отдаем HTML интерфейс"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return """
    <html>
        <body>
            <h1>RAG Поиск Комплектующих API</h1>
            <p>Version: 1.0.0</p>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/health">Health Check</a></li>
            </ul>
        </body>
    </html>
    """


@app.get("/api", response_model=Dict[str, str])
async def api_info():
    """API информация"""
    return {
        "message": "RAG Поиск Комплектующих API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья системы"""
    llm_available = processor and hasattr(processor, 'request_parser') and processor.request_parser is not None
    
    return HealthResponse(
        status="healthy" if products_loaded else "unhealthy",
        models_loaded=products_loaded,
        products_count=len(search_engine.products) if search_engine and search_engine.products else 0,
        embedding_model=search_engine.model_name if search_engine else "not loaded",
        llm_available=llm_available
    )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Поиск комплектующих по запросу (новая архитектура)
    
    Pipeline:
    1. LLM парсит запрос → список товаров + количество + top_k (динамически)
    2. Поиск каждого товара в векторной БД (с индивидуальным top_k)
    3. Расчет стоимости и формирование ответа
    
    Args:
        request: Запрос на поиск (без top_k - определяется LLM автоматически)
        
    Returns:
        SearchResponse: Результаты поиска с товарами, количеством и стоимостью
    """
    if not products_loaded or not processor:
        raise HTTPException(
            status_code=503,
            detail="Система не инициализирована. Попробуйте позже."
        )
    
    try:
        # Выполняем поиск через новую архитектуру (top_k определяется LLM)
        result = processor.process_query(
            query=request.query
        )
        
        # Формируем ответ в новом формате
        items_response = []
        for item in result.get('items', []):
            found_product = item.get('found_product')
            
            items_response.append(SearchResultItem(
                requested_item=item.get('requested_item', ''),
                quantity=item.get('quantity', 1),
                found_product=ProductInfo(
                    id=found_product.get('id', 0),
                    name=found_product.get('name', ''),
                    cost=found_product.get('cost', 0.0),
                    category=found_product.get('category', '')
                ) if found_product else None,
                relevance_score=item.get('relevance_score', 0.0),
                unit_price=item.get('unit_price', 0.0),
                total_price=item.get('total_price', 0.0),
                specifications=item.get('specifications', ''),
                alternatives=item.get('alternatives', [])
            ))
        
        return SearchResponse(
            query_id=result.get('query_id'),
            original_query=result.get('original_query', request.query),
            items=items_response,
            total_items=result.get('total_items', 0),
            found_items=result.get('found_items', 0),
            total_cost=result.get('total_cost', 0.0),
            currency=result.get('currency', 'RUB')
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при выполнении поиска: {str(e)}"
        )


@app.get("/search", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., description="Поисковый запрос", example="Комплект: короб 200x200, крышка, винты"),
    use_llm: bool = Query(True, description="Использовать LLM парсер")
):
    """
    GET эндпоинт для поиска (для удобного тестирования)
    
    Args:
        q: Поисковый запрос
        use_llm: Использовать ли LLM парсер (top_k определяется автоматически)
        
    Returns:
        SearchResponse: Результаты поиска
    """
    request = SearchRequest(
        query=q,
        use_llm=use_llm
    )
    return await search(request)


@app.get("/products/count")
async def get_products_count():
    """Получить количество товаров в базе"""
    if not products_loaded or not search_engine:
        raise HTTPException(status_code=503, detail="Система не инициализирована")
    
    return {
        "count": len(search_engine.products) if search_engine.products else 0
    }


@app.get("/products/categories")
async def get_categories():
    """Получить список категорий товаров"""
    if not products_loaded or not search_engine:
        raise HTTPException(status_code=503, detail="Система не инициализирована")
    
    try:
        categories = set()
        for product in search_engine.products:
            category = product.get('category')
            if category:
                categories.add(category)
        
        return {
            "categories": sorted(list(categories)),
            "count": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/word")
async def generate_word_document(request: SearchRequest):
    """
    Генерирует Технико-Коммерческое Предложение в формате Word (.docx)
    
    Args:
        request: Запрос на поиск (такой же как для /search)
        
    Returns:
        FileResponse: Word документ
    """
    if not products_loaded or not processor or not document_generator:
        raise HTTPException(
            status_code=503,
            detail="Система не инициализирована. Попробуйте позже."
        )
    
    try:
        # Выполняем поиск
        result = processor.process_query(query=request.query)
        
        # Генерируем документ
        filepath = document_generator.generate_word(result)
        
        return FileResponse(
            path=str(filepath),
            filename=filepath.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации документа: {str(e)}"
        )


@app.post("/generate/pdf")
async def generate_pdf_document(request: SearchRequest):
    """
    Генерирует Технико-Коммерческое Предложение в формате PDF
    
    Args:
        request: Запрос на поиск (такой же как для /search)
        
    Returns:
        FileResponse: PDF документ
    """
    if not products_loaded or not processor or not document_generator:
        raise HTTPException(
            status_code=503,
            detail="Система не инициализирована. Попробуйте позже."
        )
    
    try:
        # Выполняем поиск
        result = processor.process_query(query=request.query)
        
        # Генерируем документ
        filepath = document_generator.generate_pdf(result)
        
        # Определяем media type
        if filepath.suffix == '.pdf':
            media_type = "application/pdf"
        else:
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        return FileResponse(
            path=str(filepath),
            filename=filepath.name,
            media_type=media_type
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации документа: {str(e)}"
        )


def format_search_result_as_string(result: Dict[str, Any]) -> str:
    """
    Форматирует результат поиска в читаемую строку
    
    Args:
        result: Результат поиска от процессора
        
    Returns:
        str: Отформатированная строка с результатами
    """
    lines = []
    lines.append("=" * 70)
    lines.append("РЕЗУЛЬТАТЫ ПОИСКА")
    lines.append("=" * 70)
    lines.append("")
    
    # Исходный запрос
    lines.append(f"Запрос: {result.get('original_query', 'Не указан')}")
    lines.append("")
    
    # Статистика
    lines.append(f"Всего товаров в запросе: {result.get('total_items', 0)}")
    lines.append(f"Найдено товаров: {result.get('found_items', 0)}")
    lines.append(f"Общая стоимость: {result.get('total_cost', 0):,.2f} {result.get('currency', 'RUB')}")
    lines.append("")
    
    # Товары
    lines.append("НАЙДЕННЫЕ ТОВАРЫ:")
    lines.append("")
    
    for idx, item in enumerate(result.get('items', []), 1):
        product = item.get('found_product')
        
        lines.append(f"[{idx}] {item.get('requested_item', 'Товар')}")
        lines.append(f"    Количество: {item.get('quantity', 1)} шт.")
        
        if product:
            lines.append(f"    Найдено: {product.get('name', 'Без названия')}")
            lines.append(f"    Категория: {product.get('category', 'Не указана')}")
            lines.append(f"    Цена за ед.: {item.get('unit_price', 0):,.2f} ₽")
            lines.append(f"    Итого: {item.get('total_price', 0):,.2f} ₽")
            lines.append(f"    Релевантность: {item.get('relevance_score', 0):.4f}")
            
            # Спецификации
            if item.get('specifications'):
                lines.append(f"    Спецификация: {item.get('specifications')}")
            
            # Альтернативы
            alternatives = item.get('alternatives', [])
            if alternatives and len(alternatives) > 0:
                lines.append(f"    Альтернатив: {len(alternatives)}")
        else:
            lines.append("    ❌ Товар не найден")
        
        lines.append("")
    
    # Итоги
    lines.append("=" * 70)
    lines.append(f"ИТОГО: {result.get('total_cost', 0):,.2f} {result.get('currency', 'RUB')}")
    lines.append("=" * 70)
    
    return "\n".join(lines)


@app.post("/generate/both")
async def generate_both_documents(request: SearchRequest):
    """
    Генерирует Технико-Коммерческое Предложение в обоих форматах (Word и PDF)
    
    Args:
        request: Запрос на поиск (такой же как для /search)
        
    Returns:
        Dict: Информация о созданных документах + результат поиска в виде строки
    """
    if not products_loaded or not processor or not document_generator:
        raise HTTPException(
            status_code=503,
            detail="Система не инициализирована. Попробуйте позже."
        )
    
    try:
        # Выполняем поиск
        result = processor.process_query(query=request.query)
        
        # Генерируем документы
        files = document_generator.generate_both(result)
        
        # Форматируем результат в строку
        result_string = format_search_result_as_string(result)
        
        return {
            "message": "Документы успешно созданы",
            "files": {
                "word": {
                    "filename": files['word'].name,
                    "path": str(files['word']),
                    "download_url": f"/download/{files['word'].name}"
                },
                "pdf": {
                    "filename": files['pdf'].name,
                    "path": str(files['pdf']),
                    "download_url": f"/download/{files['pdf'].name}"
                }
            },
            "search_result": result_string,
            "search_data": {
                "original_query": result.get('original_query'),
                "total_items": result.get('total_items', 0),
                "found_items": result.get('found_items', 0),
                "total_cost": result.get('total_cost', 0.0),
                "currency": result.get('currency', 'RUB')
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации документов: {str(e)}"
        )


@app.get("/download/{filename}")
async def download_document(filename: str):
    """
    Скачать созданный документ
    
    Args:
        filename: Имя файла для скачивания
        
    Returns:
        FileResponse: Файл документа
    """
    filepath = Path("generated_documents") / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Определяем media type по расширению
    if filepath.suffix == '.pdf':
        media_type = "application/pdf"
    elif filepath.suffix == '.docx':
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type=media_type
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
