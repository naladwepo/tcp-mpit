"""
Гибридный процессор запросов с декомпозицией для сложных запросов
"""

from typing import List, Dict, Tuple, Optional
from src.llm_preprocessor import LLMQueryPreprocessor
from src.llm_request_parser import LLMRequestParser
from src.query_enhancement import QueryEnhancer
from src.llm_validator import LLMValidator, IterativeSearchValidator
from src.search_engine import VectorSearchEngine
from src.cost_calculator import create_response_json


class HybridQueryProcessor:
    """
    Процессор запросов с LLM парсером на входе
    
    Новая архитектура:
    1. LLM парсит запрос → список товаров + количество
    2. Векторный поиск для каждого товара
    3. Формирование ответа с ценами
    """
    
    def __init__(
        self, 
        search_engine: VectorSearchEngine,
        use_llm_parser: bool = True,
        llm_model_path: str = "./Qwen/Qwen3-4B-Instruct-2507",
        use_fallback_enhancement: bool = True
    ):
        """
        Args:
            search_engine: экземпляр векторного поиска
            use_llm_parser: использовать ли LLM для парсинга запроса на входе
            llm_model_path: путь к LLM модели
            use_fallback_enhancement: использовать ли QueryEnhancer как fallback
        """
        self.search_engine = search_engine
        self.use_llm_parser = use_llm_parser
        
        # LLM парсер запросов (главный компонент на входе)
        if use_llm_parser:
            self.request_parser = LLMRequestParser(
                model_path=llm_model_path,
                device=None  # Автоопределение: CUDA > MPS > CPU
            )
            print("✓ LLM Request Parser активирован")
        else:
            self.request_parser = None
        
        # Query enhancer как fallback
        if use_fallback_enhancement:
            self.query_enhancer = QueryEnhancer()
            print("✓ Query Enhancer (fallback) активирован")
        else:
            self.query_enhancer = None
    
    def process_query(
        self, 
        query: str, 
        query_id: int = None
    ) -> Dict:
        """
        Обрабатывает запрос с новой архитектурой
        
        Pipeline:
        1. LLM парсит запрос → список товаров + количество + top_k
        2. Поиск каждого товара в векторной БД (с индивидуальным top_k)
        3. Расчет стоимости и формирование ответа
        
        Args:
            query: поисковый запрос
            query_id: ID запроса
            
        Returns:
            Dict: JSON ответ с товарами, количеством и ценами
        """
        print(f"\n{'='*70}")
        print(f"📋 ОБРАБОТКА ЗАПРОСА")
        print(f"{'='*70}")
        print(f"Запрос: {query}")
        print(f"{'='*70}")
        
        # === ШАГ 1: LLM ПАРСИНГ ЗАПРОСА ===
        if self.use_llm_parser and self.request_parser:
            print("\n🤖 Шаг 1: LLM анализирует запрос...")
            parsed_request = self.request_parser.parse_request(query)
            print(self.request_parser.format_result(parsed_request))
            items_to_search = parsed_request.get('items', [])
        else:
            # Fallback на Query Enhancer
            print("\n🔍 Шаг 1: Эвристический анализ запроса...")
            if self.query_enhancer:
                enhanced = self.query_enhancer.enhance_query(query)
                items_to_search = [
                    {"name": item, "quantity": 1, "specifications": "", "top_k": 3}
                    for item in enhanced
                ]
            else:
                items_to_search = [{"name": query, "quantity": 1, "specifications": "", "top_k": 3}]
        
        # === ШАГ 2: ПОИСК КАЖДОГО ТОВАРА ===
        print(f"\n🔍 Шаг 2: Поиск товаров ({len(items_to_search)} позиций)...")
        print("-" * 70)
        
        all_results = []
        total_cost = 0
        
        for i, item_spec in enumerate(items_to_search, 1):
            item_name = item_spec.get('name', '')
            quantity = item_spec.get('quantity', 1)
            specs = item_spec.get('specifications', '')
            top_k = item_spec.get('top_k', 3)  # Динамический top_k от LLM
            
            print(f"\n{i}. Поиск: {item_name}")
            print(f"   Количество: {quantity} шт.")
            print(f"   Поиск альтернатив: {top_k}")
            
            # Поиск в векторной БД с индивидуальным top_k
            search_results = self.search_engine.search(item_name, top_k=top_k)
            
            if search_results:
                # Берем лучший результат
                best_product, best_score = search_results[0]
                
                unit_price = best_product.get('cost', 0)
                item_total = unit_price * quantity
                total_cost += item_total
                
                print(f"   ✓ Найдено: {best_product.get('name', 'N/A')[:60]}")
                print(f"   💰 Цена: {unit_price:,.0f} руб. × {quantity} = {item_total:,.0f} руб.")
                print(f"   📊 Релевантность: {best_score:.4f}")
                
                all_results.append({
                    "requested_item": item_name,
                    "quantity": quantity,
                    "found_product": best_product,
                    "relevance_score": float(best_score),
                    "unit_price": unit_price,
                    "total_price": item_total,
                    "specifications": specs,
                    "alternatives": [
                        {
                            "product": prod,
                            "score": float(score)
                        }
                        for prod, score in search_results[1:min(3, len(search_results))]
                    ]
                })
            else:
                print(f"   ❌ Товар не найден")
                all_results.append({
                    "requested_item": item_name,
                    "quantity": quantity,
                    "found_product": None,
                    "relevance_score": 0,
                    "unit_price": 0,
                    "total_price": 0,
                    "specifications": specs,
                    "alternatives": []
                })
        
        # === ШАГ 3: ФОРМИРОВАНИЕ ОТВЕТА ===
        print(f"\n{'='*70}")
        print(f"💰 ИТОГОВАЯ СТОИМОСТЬ: {total_cost:,.0f} руб.")
        print(f"{'='*70}")
        
        response = {
            "query_id": query_id,
            "original_query": query,
            "items": all_results,
            "total_items": len(items_to_search),
            "found_items": sum(1 for r in all_results if r['found_product'] is not None),
            "total_cost": total_cost,
            "currency": "RUB"
        }
        
        return response
        
        return all_results
