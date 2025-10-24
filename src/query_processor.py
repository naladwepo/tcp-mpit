"""
Главный процессор запросов - объединяет векторный поиск и LLM
"""

from typing import Dict, List, Optional
from .data_loader import DataLoader
from .search_engine import VectorSearchEngine
from .llm_generator import LLMGenerator
from .cost_calculator import create_response_json
import re


class QueryProcessor:
    """Основной класс для обработки запросов пользователей"""
    
    def __init__(
        self,
        data_dir: str = ".",
        model_path: str = "./Qwen/Qwen3-4B-Instruct-2507",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        use_llm: bool = True
    ):
        """
        Инициализация процессора
        
        Args:
            data_dir: директория с данными
            model_path: путь к Qwen модели
            embedding_model: модель для эмбеддингов
            use_llm: использовать ли LLM для фильтрации
        """
        print("="*60)
        print("Инициализация RAG-системы поиска комплектующих")
        print("="*60)
        
        # Загрузка данных
        print("\n[1/4] Загрузка данных...")
        self.data_loader = DataLoader(data_dir)
        self.products_df = self.data_loader.combine_datasets()
        print(f"✓ Загружено {len(self.products_df)} товаров")
        
        # Создание векторного индекса
        print("\n[2/4] Инициализация векторного поиска...")
        self.search_engine = VectorSearchEngine(
            model_name=embedding_model,
            index_dir=f"{data_dir}/data/index"
        )
        self.search_engine.build_index(self.products_df)
        print("✓ Векторный индекс готов")
        
        # Загрузка LLM (опционально)
        self.use_llm = use_llm
        self.llm = None
        if use_llm:
            print("\n[3/4] Загрузка LLM...")
            try:
                self.llm = LLMGenerator(model_path)
                print("✓ LLM загружен")
            except Exception as e:
                print(f"⚠ Не удалось загрузить LLM: {e}")
                print("  Будет использоваться только векторный поиск")
                self.use_llm = False
        else:
            print("\n[3/4] LLM отключен (use_llm=False)")
        
        print("\n[4/4] Система готова к работе!")
        print("="*60 + "\n")
    
    def detect_complexity(self, query: str) -> str:
        """
        Определяет сложность запроса
        
        Args:
            query: текст запроса
            
        Returns:
            str: 'simple', 'medium' или 'complex'
        """
        query_lower = query.lower()
        
        # Complex: запросы с комплектами, несколькими компонентами
        complex_keywords = ['комплект', 'набор', 'с креплением', 'для монтажа', 
                           'включая', 'полный', 'вместе с']
        if any(kw in query_lower for kw in complex_keywords):
            return 'complex'
        
        # Medium: запросы с параметрами "любой", "разных", диапазоны
        medium_keywords = ['любой', 'любая', 'любое', 'разных', 'различных',
                          'от', 'до', 'не менее', 'не более']
        if any(kw in query_lower for kw in medium_keywords):
            return 'medium'
        
        # Simple: остальные запросы
        return 'simple'
    
    def process_simple_query(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Обработка простого запроса (прямой поиск)
        
        Args:
            query: текст запроса
            top_k: количество результатов
            
        Returns:
            List[Dict]: найденные товары
        """
        # Векторный поиск с высоким порогом
        results = self.search_engine.search(query, top_k=top_k, score_threshold=0.3)
        
        # Возвращаем только товары
        return [product for product, score in results]
    
    def process_medium_query(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Обработка запроса средней сложности
        
        Args:
            query: текст запроса
            top_k: количество результатов
            
        Returns:
            List[Dict]: найденные товары
        """
        # Получаем больше кандидатов с более низким порогом
        results = self.search_engine.search(query, top_k=top_k * 2, score_threshold=0.2)
        
        candidates = [product for product, score in results]
        
        # Если есть LLM, используем его для фильтрации
        if self.use_llm and self.llm:
            selected = self.llm.select_products(query, candidates, max_candidates=15)
            if selected:
                return selected[:top_k]
        
        # Иначе возвращаем top результаты
        return candidates[:top_k]
    
    def process_complex_query(
        self,
        query: str,
        top_k: int = 15
    ) -> List[Dict]:
        """
        Обработка сложного запроса (комплекты)
        
        Args:
            query: текст запроса
            top_k: количество результатов
            
        Returns:
            List[Dict]: найденные товары
        """
        # Получаем много кандидатов
        results = self.search_engine.search(query, top_k=top_k * 3, score_threshold=0.15)
        
        candidates = [product for product, score in results]
        
        # Для комплектов обязательно используем LLM
        if self.use_llm and self.llm:
            selected = self.llm.select_products(query, candidates, max_candidates=20)
            if selected:
                return selected
        
        # Без LLM пытаемся найти связанные товары по категориям
        # Извлекаем ключевые слова из запроса
        return self._select_related_products(query, candidates, top_k)
    
    def _select_related_products(
        self,
        query: str,
        candidates: List[Dict],
        max_items: int
    ) -> List[Dict]:
        """
        Выбирает связанные товары из кандидатов (fallback без LLM)
        
        Args:
            query: запрос
            candidates: список кандидатов
            max_items: максимальное количество
            
        Returns:
            List[Dict]: выбранные товары
        """
        # Простая эвристика: берем товары разных категорий
        selected = []
        seen_categories = set()
        
        for product in candidates:
            category = product.get('category', '')
            
            # Добавляем, если категория новая или очень релевантна
            if category not in seen_categories or len(selected) < 3:
                selected.append(product)
                seen_categories.add(category)
            
            if len(selected) >= max_items:
                break
        
        return selected
    
    def process_query(
        self,
        query: str,
        complexity: Optional[str] = None,
        query_id: Optional[int] = None
    ) -> Dict:
        """
        Главная функция обработки запроса
        
        Args:
            query: текст запроса
            complexity: явная сложность ('simple'/'medium'/'complex')
            query_id: ID запроса
            
        Returns:
            Dict: структурированный ответ в формате JSON
        """
        # Определяем сложность, если не указана
        if complexity is None:
            complexity = self.detect_complexity(query)
        
        print(f"\nОбработка запроса [{complexity}]: '{query}'")
        
        # Выбираем стратегию обработки
        if complexity == 'simple':
            found_items = self.process_simple_query(query, top_k=10)
        elif complexity == 'medium':
            found_items = self.process_medium_query(query, top_k=10)
        else:  # complex
            found_items = self.process_complex_query(query, top_k=15)
        
        print(f"Найдено товаров: {len(found_items)}")
        
        # Формируем ответ
        response = create_response_json(
            found_items=found_items,
            query_id=query_id,
            complexity=complexity
        )
        
        return response


if __name__ == "__main__":
    # Тестирование
    processor = QueryProcessor(
        use_llm=False  # Для быстрого теста без LLM
    )
    
    # Тестовые запросы
    test_queries = [
        ("Гайка М6", "simple"),
        ("Короб 100x100 мм любой длины", "medium"),
        ("Комплект для монтажа короба 200x200: короб, крышка, винты и гайки", "complex")
    ]
    
    for query, expected_complexity in test_queries:
        print("\n" + "="*60)
        response = processor.process_query(query)
        
        import json
        print(json.dumps(response, ensure_ascii=False, indent=2))
