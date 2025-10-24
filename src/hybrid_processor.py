"""
Гибридный процессор запросов с декомпозицией для сложных запросов
"""

from typing import List, Dict, Tuple
from src.llm_preprocessor import LLMQueryPreprocessor
from src.search_engine import VectorSearchEngine
from src.cost_calculator import create_response_json


class HybridQueryProcessor:
    """
    Процессор запросов с автоматической декомпозицией сложных запросов
    """
    
    def __init__(
        self, 
        search_engine: VectorSearchEngine,
        use_llm: bool = True,
        llm_model_path: str = "./Qwen/Qwen3-4B-Instruct-2507"
    ):
        """
        Args:
            search_engine: экземпляр векторного поиска
            use_llm: использовать ли LLM для препроцессинга
            llm_model_path: путь к LLM модели
        """
        self.search_engine = search_engine
        self.use_llm_flag = use_llm
        
        # Всегда создаем препроцессор (он имеет fallback)
        self.preprocessor = LLMQueryPreprocessor(
            model_path=llm_model_path,
            use_llm=use_llm
        )
    
    def process_query(
        self, 
        query: str, 
        top_k: int = 10,
        complexity: str = None,
        query_id: int = None,
        use_decomposition: bool = True
    ) -> Dict:
        """
        Обрабатывает запрос с автоматической декомпозицией
        
        Args:
            query: поисковый запрос
            top_k: количество результатов
            complexity: сложность запроса (простой/средний/сложный)
            query_id: ID запроса
            use_decomposition: использовать ли декомпозицию для сложных запросов
            
        Returns:
            Dict: JSON ответ
        """
        # Проверяем нужна ли декомпозиция
        if not use_decomposition or not self.preprocessor:
            # Простой поиск без декомпозиции
            results = self.search_engine.search(query, top_k=top_k)
            found_items = [product for product, score in results]
        else:
            # Используем препроцессор для разбиения запроса
            components = self.preprocessor.decompose_query(query)
            
            if len(components) == 1:
                # Простой запрос - ищем как обычно
                results = self.search_engine.search(query, top_k=top_k)
                found_items = [product for product, score in results]
            else:
                # Сложный запрос - ищем по компонентам
                print(f"Найдено компонентов: {len(components)}")
                for i, comp in enumerate(components, 1):
                    print(f"  {i}. {comp}")
                # По 2 товара на компонент для сбалансированного результата
                found_items = self._search_by_components(components, items_per_component=2)
                # Ограничиваем общее количество (для сложных запросов берем по 1.5x на компонент)
                max_items = min(top_k, len(components) * 2)
                found_items = found_items[:max_items]
        
        # Создаем ответ
        response = create_response_json(
            found_items=found_items,
            query_id=query_id,
            complexity=complexity
        )
        
        return response
    
    def _search_by_components(
        self, 
        components: List[str], 
        items_per_component: int = 2
    ) -> List[Dict]:
        """
        Поиск по компонентам запроса
        
        Args:
            components: список компонентов запроса (строки)
            items_per_component: сколько элементов искать для каждого компонента
            
        Returns:
            List[Dict]: объединенный список найденных товаров
        """
        all_results = []
        seen_ids = set()
        
        for component in components:
            # Ищем по компоненту
            results = self.search_engine.search(
                component, 
                top_k=items_per_component
            )
            
            # Добавляем результаты без дубликатов
            for product, score in results:
                product_id = product.get('id')
                if product_id not in seen_ids:
                    all_results.append(product)
                    seen_ids.add(product_id)
        
        return all_results
