"""
LLM Validator - финальная обработка результатов поиска
Анализирует соответствие найденных товаров запросу, рассчитывает количество и стоимость
"""

import json
import re
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path


class LLMValidator:
    """
    LLM валидатор для финальной обработки результатов поиска
    
    Функции:
    1. Проверяет соответствие найденных товаров запросу
    2. Определяет необходимое количество каждого товара
    3. Рассчитывает итоговую стоимость
    4. Может запросить дополнительный поиск если чего-то не хватает
    """
    
    def __init__(
        self, 
        model_path: str = "./Qwen/Qwen3-4B-Instruct-2507",
        use_llm: bool = True
    ):
        """
        Args:
            model_path: путь к LLM модели
            use_llm: использовать ли LLM (False = простые эвристики)
        """
        self.model_path = Path(model_path)
        self.model = None
        self.tokenizer = None
        self.use_llm = use_llm
        
        if use_llm and self.model_path.exists():
            self._load_model()
        else:
            print("📝 LLM Validator работает в режиме эвристик (без LLM)")
    
    def _load_model(self):
        """Загрузка LLM модели"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            print(f"Загрузка LLM валидатора из {self.model_path}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                device_map="cpu",
                torch_dtype=torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            print("✓ LLM валидатор загружен")
            
        except Exception as e:
            print(f"⚠️ Не удалось загрузить LLM валидатор: {e}")
            print("Будут использоваться простые эвристики")
            self.model = None
            self.tokenizer = None
    
    def validate_and_calculate(
        self,
        original_query: str,
        found_items: List[Dict[str, Any]],
        max_iterations: int = 2
    ) -> Dict[str, Any]:
        """
        Главный метод: валидирует результаты и рассчитывает стоимость
        
        Args:
            original_query: исходный запрос пользователя
            found_items: найденные товары [{"name": ..., "cost": ...}, ...]
            max_iterations: максимум итераций для дополнительного поиска
            
        Returns:
            Dict с результатами валидации, расчётами и возможными дополнительными запросами
        """
        if self.model is None or self.tokenizer is None:
            # Режим эвристик
            return self._heuristic_validation(original_query, found_items)
        
        try:
            return self._llm_validation(original_query, found_items, max_iterations)
        except Exception as e:
            print(f"⚠️ Ошибка LLM валидации: {e}")
            return self._heuristic_validation(original_query, found_items)
    
    def _llm_validation(
        self,
        original_query: str,
        found_items: List[Dict[str, Any]],
        max_iterations: int
    ) -> Dict[str, Any]:
        """
        Валидация через LLM
        """
        # Форматируем найденные товары
        items_text = "\n".join([
            f"{i+1}. {item['name']} - {item.get('cost', 'N/A')} руб."
            for i, item in enumerate(found_items)
        ])
        
        prompt = f"""Ты - эксперт по подбору строительных материалов и комплектующих.

Задача: проанализируй запрос пользователя и найденные товары. Определи:
1. Какие товары соответствуют запросу
2. Сколько единиц каждого товара нужно
3. Чего не хватает (если что-то нужно, но не найдено)

ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{original_query}

НАЙДЕННЫЕ ТОВАРЫ:
{items_text}

ИНСТРУКЦИИ:
- Для комплектов (короб + крышка + крепеж): обычно нужны 1 короб, 1 крышка, 4 винта, 4 гайки
- Для монтажа коробов 200x200: 4 винта М6 и 4 гайки М6
- Для монтажа лотков: количество зависит от длины (обычно каждые 50см - 1 крепление)
- Если пользователь указал количество явно - используй его
- Если не указано - рассчитай стандартное количество

ФОРМАТ ОТВЕТА (JSON):
{{
  "analysis": "краткий анализ запроса",
  "selected_items": [
    {{
      "item_index": 0,  // индекс товара из списка (начиная с 0)
      "name": "название товара",
      "quantity": 2,  // сколько единиц нужно
      "unit_price": 150,  // цена за единицу
      "total_price": 300,  // общая стоимость (quantity * unit_price)
      "reason": "почему выбран и почему такое количество"
    }}
  ],
  "missing_items": [
    // список того, чего не хватает (если нужно)
    {{
      "description": "что нужно найти",
      "reason": "почему это нужно"
    }}
  ],
  "total_cost": 1500,  // общая стоимость всех выбранных товаров
  "confidence": 0.9  // уверенность в результате (0.0-1.0)
}}

JSON:"""

        # Генерация ответа
        messages = [
            {"role": "system", "content": "Ты - эксперт по подбору строительных материалов."},
            {"role": "user", "content": prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=1024,
            temperature=0.3,
            do_sample=True,
            top_p=0.9
        )
        
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Парсим JSON ответ
        result = self._parse_llm_validation_response(response, found_items)
        
        if result:
            print(f"✓ LLM валидация: найдено {len(result['selected_items'])} релевантных товаров")
            if result.get('missing_items'):
                print(f"⚠️ Не хватает: {len(result['missing_items'])} позиций")
            return result
        else:
            print("⚠️ Не удалось распарсить ответ LLM, используем эвристики")
            return self._heuristic_validation(original_query, found_items)
    
    def _parse_llm_validation_response(
        self, 
        response: str, 
        found_items: List[Dict]
    ) -> Optional[Dict]:
        """
        Парсит JSON ответ от LLM
        """
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                # Валидируем структуру
                if 'selected_items' in data and 'total_cost' in data:
                    # Добавляем полные данные о товарах
                    for item in data['selected_items']:
                        idx = item.get('item_index', -1)
                        if 0 <= idx < len(found_items):
                            item['full_data'] = found_items[idx]
                    
                    return data
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            return None
    
    def _heuristic_validation(
        self,
        original_query: str,
        found_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Простая эвристическая валидация без LLM
        
        Правила:
        - Берем все найденные товары
        - Для комплектов: 1 основной товар, 1 крышка, 4 винта, 4 гайки
        - Для простых запросов: 1 единица каждого товара
        """
        query_lower = original_query.lower()
        
        # Определяем тип запроса
        is_assembly = any(kw in query_lower for kw in ['комплект', 'набор', 'монтаж', 'установка'])
        
        selected_items = []
        total_cost = 0
        
        for idx, item in enumerate(found_items):
            name_lower = item['name'].lower()
            unit_price = item.get('cost', 0)
            
            # Определяем количество
            if is_assembly:
                # Для комплектов
                if any(word in name_lower for word in ['винт', 'болт']):
                    quantity = 4  # 4 винта для монтажа
                elif 'гайк' in name_lower:
                    quantity = 4  # 4 гайки
                elif any(word in name_lower for word in ['шайб']):
                    quantity = 4  # 4 шайбы
                elif any(word in name_lower for word in ['короб', 'лоток', 'корпус', 'крышка']):
                    quantity = 1  # 1 основной элемент
                else:
                    quantity = 1
            else:
                # Для простых запросов - по 1 единице
                quantity = 1
            
            total_price = unit_price * quantity
            total_cost += total_price
            
            selected_items.append({
                "item_index": idx,
                "name": item['name'],
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
                "reason": "выбрано эвристически",
                "full_data": item
            })
        
        return {
            "analysis": f"Эвристический анализ: {'комплект' if is_assembly else 'простой запрос'}",
            "selected_items": selected_items,
            "missing_items": [],
            "total_cost": total_cost,
            "confidence": 0.7,  # Средняя уверенность для эвристик
            "method": "heuristic"
        }
    
    def format_result(self, validation_result: Dict) -> str:
        """
        Форматирует результат валидации в читаемый текст
        """
        lines = []
        lines.append("=" * 60)
        lines.append("📊 РЕЗУЛЬТАТЫ АНАЛИЗА")
        lines.append("=" * 60)
        
        if 'analysis' in validation_result:
            lines.append(f"\n💡 Анализ: {validation_result['analysis']}")
        
        lines.append(f"\n✅ ВЫБРАННЫЕ ТОВАРЫ ({len(validation_result['selected_items'])} поз.):")
        lines.append("-" * 60)
        
        for i, item in enumerate(validation_result['selected_items'], 1):
            lines.append(f"\n{i}. {item['name']}")
            lines.append(f"   Количество: {item['quantity']} шт.")
            lines.append(f"   Цена за ед.: {item['unit_price']:,} руб.")
            lines.append(f"   Итого: {item['total_price']:,} руб.")
            if 'reason' in item:
                lines.append(f"   Обоснование: {item['reason']}")
        
        if validation_result.get('missing_items'):
            lines.append(f"\n⚠️ НЕ ХВАТАЕТ ({len(validation_result['missing_items'])} поз.):")
            lines.append("-" * 60)
            for i, missing in enumerate(validation_result['missing_items'], 1):
                lines.append(f"\n{i}. {missing['description']}")
                if 'reason' in missing:
                    lines.append(f"   Причина: {missing['reason']}")
        
        lines.append(f"\n{'=' * 60}")
        lines.append(f"💰 ОБЩАЯ СТОИМОСТЬ: {validation_result['total_cost']:,} руб.")
        lines.append(f"🎯 Уверенность: {validation_result.get('confidence', 0):.0%}")
        lines.append("=" * 60)
        
        return "\n".join(lines)


class IterativeSearchValidator(LLMValidator):
    """
    Расширенная версия валидатора с возможностью итеративного поиска
    
    Если LLM определяет, что чего-то не хватает - делает дополнительный запрос к поиску
    """
    
    def __init__(self, *args, search_engine=None, **kwargs):
        """
        Args:
            search_engine: экземпляр VectorSearchEngine для дополнительных запросов
        """
        super().__init__(*args, **kwargs)
        self.search_engine = search_engine
    
    def validate_with_iterative_search(
        self,
        original_query: str,
        initial_items: List[Dict[str, Any]],
        max_iterations: int = 2,
        items_per_search: int = 3
    ) -> Dict[str, Any]:
        """
        Валидация с возможностью дополнительного поиска
        
        Args:
            original_query: исходный запрос
            initial_items: начальные найденные товары
            max_iterations: максимум итераций дополнительного поиска
            items_per_search: сколько товаров искать в каждой итерации
            
        Returns:
            Финальный результат с учётом всех итераций
        """
        if not self.search_engine:
            print("⚠️ Search engine не настроен, итеративный поиск невозможен")
            return self.validate_and_calculate(original_query, initial_items)
        
        all_found_items = initial_items.copy()
        iteration = 0
        
        print(f"\n🔍 ИТЕРАТИВНЫЙ ПОИСК (макс. {max_iterations} итераций)")
        print("=" * 60)
        
        while iteration < max_iterations:
            print(f"\n📍 Итерация {iteration + 1}/{max_iterations}")
            
            # Валидируем текущие результаты
            result = self.validate_and_calculate(original_query, all_found_items)
            
            # Проверяем, нужен ли дополнительный поиск
            missing = result.get('missing_items', [])
            
            if not missing:
                print("✓ Все необходимые товары найдены!")
                break
            
            print(f"⚠️ Не хватает: {len(missing)} позиций")
            
            # Выполняем дополнительный поиск для каждого недостающего товара
            new_items_found = False
            for missing_item in missing:
                search_query = missing_item['description']
                print(f"   🔎 Ищем: {search_query}")
                
                # Поиск через search engine
                search_results = self.search_engine.search(
                    search_query, 
                    top_k=items_per_search
                )
                
                # Добавляем новые товары (если их еще нет)
                for product, score in search_results:
                    product_dict = {
                        'id': product.id,
                        'name': product.name,
                        'cost': product.cost,
                        'similarity': score
                    }
                    
                    # Проверяем дубликаты
                    if not any(item['id'] == product.id for item in all_found_items):
                        all_found_items.append(product_dict)
                        new_items_found = True
                        print(f"      ✓ Добавлен: {product.name} ({score:.2f})")
            
            if not new_items_found:
                print("⚠️ Новых товаров не найдено, завершаем поиск")
                break
            
            iteration += 1
        
        # Финальная валидация
        print(f"\n✅ ФИНАЛЬНАЯ ВАЛИДАЦИЯ")
        print(f"Всего найдено товаров: {len(all_found_items)}")
        final_result = self.validate_and_calculate(original_query, all_found_items)
        final_result['iterations'] = iteration + 1
        final_result['total_items_found'] = len(all_found_items)
        
        return final_result


# Тестирование
if __name__ == "__main__":
    # Пример данных
    test_query = "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки"
    
    test_items = [
        {"id": 1, "name": "Короб IP65 200x200", "cost": 1500},
        {"id": 2, "name": "Крышка глухая 200", "cost": 300},
        {"id": 3, "name": "Винт М6×20", "cost": 5},
        {"id": 4, "name": "Гайка М6", "cost": 2},
    ]
    
    # Тест с эвристиками
    validator = LLMValidator(use_llm=False)
    result = validator.validate_and_calculate(test_query, test_items)
    
    print(validator.format_result(result))
