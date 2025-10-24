"""
FastAPI приложение для RAG-поиска комплектующих
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from pathlib import Path

from src.data_loader import DataLoader
from src.search_engine import VectorSearchEngine
from src.hybrid_processor import HybridQueryProcessor

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


# Pydantic модели
class SearchRequest(BaseModel):
    """Запрос на поиск"""
    query: str = Field(..., description="Поисковый запрос", example="Гайка М6")
    top_k: int = Field(10, description="Количество результатов", ge=1, le=50)
    use_decomposition: bool = Field(True, description="Использовать декомпозицию для сложных запросов")
    complexity: Optional[str] = Field(None, description="Сложность запроса (simple/medium/complex)")


class FoundItem(BaseModel):
    """Найденный товар"""
    name: str
    cost: str


class SearchResponse(BaseModel):
    """Ответ на поиск"""
    found_items: List[FoundItem]
    items_count: int
    total_cost: str
    query: str


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
    global search_engine, processor, products_loaded
    
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
        
        # Создаем гибридный процессор с LLM
        print("🤖 Инициализация гибридного процессора...")
        processor = HybridQueryProcessor(
            search_engine=search_engine,
            use_llm=True
        )
        
        products_loaded = True
        print("=" * 70)
        print("✅ RAG API готов к работе!")
        print(f"📊 Модель эмбеддингов: {embedding_model}")
        print(f"🗂️  Индекс: {index_dir}")
        print(f"📦 Товаров в базе: {len(products_df)}")
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
    llm_available = processor and processor.preprocessor and processor.preprocessor.model is not None
    
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
    Поиск комплектующих по запросу
    
    Args:
        request: Запрос на поиск
        
    Returns:
        SearchResponse: Результаты поиска с товарами и стоимостью
    """
    if not products_loaded or not processor:
        raise HTTPException(
            status_code=503,
            detail="Система не инициализирована. Попробуйте позже."
        )
    
    try:
        # Выполняем поиск через гибридный процессор
        result = processor.process_query(
            query=request.query,
            top_k=request.top_k,
            use_decomposition=request.use_decomposition,
            complexity=request.complexity
        )
        
        # Формируем ответ
        response_data = result.get('response', {})
        
        return SearchResponse(
            found_items=[
                FoundItem(name=item['name'], cost=item['cost'])
                for item in response_data.get('found_items', [])
            ],
            items_count=response_data.get('items_count', 0),
            total_cost=response_data.get('total_cost', '0 руб.'),
            query=request.query
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при выполнении поиска: {str(e)}"
        )


@app.get("/search", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., description="Поисковый запрос", example="Гайка М6"),
    top_k: int = Query(10, description="Количество результатов", ge=1, le=50),
    decompose: bool = Query(True, description="Использовать декомпозицию")
):
    """
    GET эндпоинт для поиска (для удобного тестирования)
    
    Args:
        q: Поисковый запрос
        top_k: Количество результатов
        decompose: Использовать ли декомпозицию
        
    Returns:
        SearchResponse: Результаты поиска
    """
    request = SearchRequest(
        query=q,
        top_k=top_k,
        use_decomposition=decompose
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


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
