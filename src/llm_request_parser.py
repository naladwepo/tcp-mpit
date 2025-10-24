"""
LLM-парсер запросов: анализирует запрос и выдает структурированный список товаров
"""

import json
import re
from typing import List, Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class LLMRequestParser:
    """
    Использует LLM для разбора запроса пользователя
    
    Выдает структурированный JSON:
    {
        "items": [
            {"name": "Короб 200x200", "quantity": 1, "specifications": "200x200 мм", "top_k": 3},
            {"name": "Крышка", "quantity": 1, "specifications": "200 мм", "top_k": 3},
            {"name": "Винт М6", "quantity": 4, "specifications": "М6", "top_k": 5},
            {"name": "Гайка М6", "quantity": 4, "specifications": "М6", "top_k": 5}
        ]
    }
    
    top_k - количество альтернатив для поиска (1-10):
    - Для специфичных товаров (с точными размерами): 2-3
    - Для стандартных товаров (крепеж, метизы): 5-7
    - Для общих запросов: 3-5
    """
    
    def __init__(
        self,
        model_path: str = "Qwen/Qwen3-4B-Instruct-2507",
        device: Optional[str] = None
    ):
        """
        Инициализация LLM парсера
        
        Args:
            model_path: путь к LLM модели
            device: устройство ('cuda', 'mps', 'cpu') или None для автоопределения
        """
        self.model_path = model_path
        self.device = self._detect_device(device)
        self.model = None
        self.tokenizer = None
        
        print(f"🖥️  Используется устройство: {self.device}")
        self._load_model()
    
    def _detect_device(self, device: Optional[str] = None) -> str:
        """
        Автоматически определяет лучшее доступное устройство
        
        Приоритет: CUDA > MPS > CPU
        
        Args:
            device: явно указанное устройство или None
            
        Returns:
            str: название устройства ('cuda', 'mps', 'cpu')
        """
        if device:
            return device
        
        # Проверяем CUDA (NVIDIA GPU)
        if torch.cuda.is_available():
            print("✓ Обнаружена CUDA (NVIDIA GPU)")
            return "cuda"
        
        # Проверяем MPS (Apple Silicon GPU)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("✓ Обнаружен MPS (Apple Silicon GPU)")
            return "mps"
        
        # Fallback на CPU
        print("ℹ️  GPU не обнаружен, используется CPU")
        return "cpu"
    
    def _load_model(self):
        """Загружает LLM модель с поддержкой CUDA/MPS/CPU"""
        print(f"Загрузка LLM парсера из {self.model_path}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        print("✓ Токенизатор загружен")
        
        # Определяем dtype в зависимости от устройства
        if self.device == "cuda":
            torch_dtype = torch.float16
            device_map = "auto"
        elif self.device == "mps":
            torch_dtype = torch.float16
            device_map = None
        else:  # CPU
            torch_dtype = torch.float32
            device_map = None
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map=device_map if self.device == "cuda" else None,
            torch_dtype=torch_dtype,
            trust_remote_code=True
        )
        
        # Явно переносим на устройство если не используем device_map
        if self.device != "cuda":
            self.model = self.model.to(self.device)
        
        print(f"✓ LLM парсер загружен на {self.device}")
    
    def parse_request(self, user_query: str) -> Dict:
        """
        Парсит запрос пользователя и возвращает структурированный список товаров
        
        Args:
            user_query: запрос пользователя
            
        Returns:
            Dict с ключами:
                - items: List[Dict] - список товаров с количеством
                - confidence: float - уверенность в разборе (0-1)
                - analysis: str - краткий анализ запроса
        """
        prompt = self._build_prompt(user_query)
        
        # Генерация ответа от LLM
        response = self._generate(prompt)
        
        # Парсинг JSON из ответа
        parsed = self._parse_response(response)
        
        if parsed:
            return parsed
        else:
            # Fallback: эвристический парсинг
            return self._heuristic_parse(user_query)
    
    def _build_prompt(self, user_query: str) -> str:
        """Создает промпт для LLM"""
        prompt = f"""Ты - эксперт по анализу запросов для поиска электротехнической продукции.

Твоя задача: разобрать запрос пользователя и выдать структурированный список товаров с количеством.

ПРАВИЛА:
1. Определи ВСЕ товары, которые нужны пользователю
2. Укажи точное количество каждого товара
3. Определи top_k (количество альтернатив для поиска, 1-10):
   - Для товаров с точными размерами и спецификациями: 2-3
   - Для стандартного крепежа (винты, гайки, шайбы): 5-7
   - Для общих запросов без точных характеристик: 3-5
4. Для комплектов монтажа используй стандарты:
   - Короб/лоток: 1 шт, top_k: 3
   - Крышка: 1 шт, top_k: 3
   - Винты: 4 шт, top_k: 5 (стандарт для монтажа)
   - Гайки: 4 шт, top_k: 5 (если нужны)
   - Шайбы: 4 шт, top_k: 5 (если нужны)
5. Сохраняй спецификации (размеры, резьбу, материал)

ФОРМАТ ОТВЕТА (только JSON, без дополнительного текста):
{{
    "items": [
        {{"name": "название товара", "quantity": число, "specifications": "технические характеристики", "top_k": 1-10}},
        ...
    ],
    "confidence": 0.0-1.0,
    "analysis": "краткий анализ запроса"
}}

ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{user_query}

ОТВЕТ (только JSON):"""
        
        return prompt
    
    def _generate(self, prompt: str) -> str:
        """Генерирует ответ от LLM"""
        messages = [
            {"role": "system", "content": "Ты - эксперт по анализу запросов для поиска товаров. Отвечаешь только в формате JSON."},
            {"role": "user", "content": prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
        
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=512,
            temperature=0.3,
            top_p=0.9,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response
    
    def _parse_response(self, response: str) -> Optional[Dict]:
        """Парсит JSON из ответа LLM"""
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                # Валидация структуры
                if 'items' in data and isinstance(data['items'], list):
                    # Проверяем каждый товар
                    for item in data['items']:
                        if 'name' not in item or 'quantity' not in item:
                            return None
                    
                    return data
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            return None
    
    def _heuristic_parse(self, user_query: str) -> Dict:
        """
        Эвристический парсинг запроса (fallback если LLM не справилась)
        """
        query_lower = user_query.lower()
        items = []
        
        # Проверяем тип запроса
        is_assembly = any(kw in query_lower for kw in ['комплект', 'монтаж', 'установка', 'набор'])
        
        # Базовые паттерны товаров
        patterns = [
            (r'короб\s*(\d+x\d+)?', 'Короб', 1, 3),  # (pattern, name, default_qty, top_k)
            (r'крышк[аи]', 'Крышка', 1, 3),
            (r'винт[ы]?\s*(М\d+)?', 'Винт', 4 if is_assembly else 1, 5),
            (r'гайк[аи]?\s*(М\d+)?', 'Гайка', 4 if is_assembly else 1, 5),
            (r'шайб[аы]?\s*(М\d+)?', 'Шайба', 4 if is_assembly else 1, 5),
            (r'лоток\s*(\d+)?', 'Лоток', 1, 3),
        ]
        
        for pattern, name, default_qty, default_top_k in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                # Проверяем, указано ли количество явно
                qty_match = re.search(rf'(\d+)\s+{pattern}', query_lower)
                quantity = int(qty_match.group(1)) if qty_match else default_qty
                
                # Извлекаем спецификации
                specs = match.group(1) if match.lastindex else ""
                
                items.append({
                    "name": f"{name} {specs}".strip(),
                    "quantity": quantity,
                    "specifications": specs,
                    "top_k": default_top_k
                })
        
        return {
            "items": items if items else [{"name": user_query, "quantity": 1, "specifications": "", "top_k": 3}],
            "confidence": 0.6,  # Средняя уверенность для эвристик
            "analysis": f"Эвристический анализ: найдено {len(items)} позиций"
        }
    
    def format_result(self, parsed_result: Dict) -> str:
        """Форматирует результат парсинга для вывода"""
        lines = []
        lines.append("=" * 60)
        lines.append("📋 АНАЛИЗ ЗАПРОСА")
        lines.append("=" * 60)
        lines.append(f"\n💡 {parsed_result.get('analysis', 'N/A')}")
        lines.append(f"🎯 Уверенность: {parsed_result.get('confidence', 0) * 100:.0f}%")
        lines.append(f"\n📦 ТОВАРЫ К ПОИСКУ ({len(parsed_result.get('items', []))} поз.):")
        lines.append("-" * 60)
        
        for i, item in enumerate(parsed_result.get('items', []), 1):
            name = item.get('name', 'N/A')
            qty = item.get('quantity', 1)
            specs = item.get('specifications', '')
            top_k = item.get('top_k', 3)
            
            lines.append(f"\n{i}. {name}")
            lines.append(f"   Количество: {qty} шт.")
            if specs:
                lines.append(f"   Спецификация: {specs}")
            lines.append(f"   Альтернатив для поиска: {top_k}")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# Пример использования
if __name__ == "__main__":
    parser = LLMRequestParser()
    
    test_queries = [
        "Короб 200x200",
        "Комплект для монтажа короба: короб 200x200, крышка, винты М6 и гайки М6",
        "Нужен лоток 600 мм с крышкой",
        "5 гаек М8 и 5 винтов М8"
    ]
    
    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"ЗАПРОС: {query}")
        print('='*70)
        
        result = parser.parse_request(query)
        print(parser.format_result(result))
