"""
LLM-based препроцессинг запросов для разбиения на компоненты
"""

import json
import re
from typing import List, Dict, Optional
from pathlib import Path


class LLMQueryPreprocessor:
    """
    Использует LLM для разбиения сложных запросов на компоненты
    """
    
    def __init__(self, model_path: str = "./Qwen/Qwen3-4B-Instruct-2507", use_llm: bool = True):
        """
        Args:
            model_path: путь к модели Qwen
            use_llm: пытаться ли загружать LLM (False = сразу использовать простой парсер)
        """
        self.model_path = Path(model_path)
        self.model = None
        self.tokenizer = None
        self.use_llm = use_llm
        
        if use_llm:
            self._load_model()
        else:
            print("📝 LLM отключен, используется простой парсер")
    
    def _load_model(self):
        """Ленивая загрузка модели"""
        # Проверяем существование пути к модели
        if not self.model_path.exists():
            print(f"⚠️ Путь к LLM модели не найден: {self.model_path}")
            print("Будет использоваться простой парсер без LLM")
            self.model = None
            return
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            print(f"Загрузка LLM модели из {self.model_path}...")
            
            # Сначала пытаемся загрузить токенизатор
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    str(self.model_path),
                    trust_remote_code=True
                )
                print("✓ Токенизатор загружен")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки токенизатора: {e}")
                raise
            
            # Затем загружаем модель
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    str(self.model_path),
                    device_map="cpu",
                    torch_dtype=torch.float32,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
                print("✓ LLM модель загружена успешно")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки модели: {e}")
                raise
            
        except ImportError as e:
            print(f"⚠️ Не установлены необходимые библиотеки: {e}")
            print("Установите: pip install transformers torch")
            print("Будет использоваться простой парсер без LLM")
            self.model = None
            self.tokenizer = None
            
        except Exception as e:
            error_msg = str(e)
            if "ModelWrapper" in error_msg:
                print(f"⚠️ Несовместимая версия transformers для модели Qwen3")
                print("Qwen3 требует transformers >= 4.51.0")
                
                # Проверяем текущую версию
                try:
                    import transformers
                    current_version = transformers.__version__
                    print(f"Текущая версия: {current_version}")
                except:
                    pass
                
                print("Обновите: pip install --upgrade transformers")
            elif "safetensors" in error_msg.lower():
                print(f"⚠️ Проблема с файлами модели (safetensors)")
            else:
                print(f"⚠️ Не удалось загрузить LLM: {error_msg[:100]}")
            
            print("Будет использоваться простой парсер без LLM")
            self.model = None
            self.tokenizer = None
    
    def decompose_query(self, query: str) -> List[str]:
        """
        Разбивает запрос на компоненты используя LLM
        
        Args:
            query: исходный запрос
            
        Returns:
            List[str]: список компонентов
        """
        # Если LLM недоступен, используем простой парсер
        if self.model is None or self.tokenizer is None:
            return self._simple_decompose(query)
        
        try:
            # Промпт для LLM
            prompt = f"""Ты - эксперт по анализу запросов на поиск строительных материалов.

Задача: разбей сложный запрос на отдельные компоненты для поиска.

Правила:
1. Извлеки каждый отдельный товар из запроса
2. Сохрани важные параметры (размеры, материал)
3. Для крепежа (винты, гайки) используй стандартные обозначения (М6, М8, М10)
4. Верни результат в виде JSON списка строк

Пример 1:
Запрос: "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки"
Результат: ["Короб 200x200", "Крышка 200", "Винт М6", "Гайка М6"]

Пример 2:
Запрос: "Лоток перфорированный 600 мм"
Результат: ["Лоток перфорированный 600 мм"]

Пример 3:
Запрос: "Гайка М6"
Результат: ["Гайка М6"]

Запрос: "{query}"
Результат:"""

            # Генерация
            messages = [
                {"role": "system", "content": "Ты - помощник для разбиения запросов на компоненты."},
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
                max_new_tokens=256,
                temperature=0.1,
                do_sample=False
            )
            
            generated_ids = [
                output_ids[len(input_ids):] 
                for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Парсим JSON ответ
            components = self._parse_llm_response(response)
            
            if components:
                print(f"✓ LLM разбил запрос на {len(components)} компонента(ов)")
                for i, comp in enumerate(components, 1):
                    print(f"  {i}. {comp}")
                return components
            else:
                # Fallback если LLM не смог распарсить
                print("⚠️ LLM не смог распарсить ответ, используется простой парсер")
                return self._simple_decompose(query)
                
        except Exception as e:
            print(f"⚠️ Ошибка при использовании LLM для декомпозиции: {e}")
            print("Переключение на простой парсер...")
            return self._simple_decompose(query)
    
    def _parse_llm_response(self, response: str) -> Optional[List[str]]:
        """Парсит ответ LLM"""
        try:
            # Ищем JSON массив в ответе
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                components = json.loads(json_match.group(0))
                if isinstance(components, list) and all(isinstance(c, str) for c in components):
                    return [c.strip() for c in components if c.strip()]
            
            # Пробуем построчно
            lines = response.strip().split('\n')
            components = []
            for line in lines:
                line = line.strip()
                # Убираем маркеры списка
                line = re.sub(r'^[-*•]\s*', '', line)
                line = re.sub(r'^\d+\.\s*', '', line)
                # Убираем кавычки
                line = line.strip('"\'')
                if line and len(line) > 2:
                    components.append(line)
            
            if components:
                return components
            
        except Exception as e:
            print(f"Ошибка парсинга ответа LLM: {e}")
        
        return None
    
    def _simple_decompose(self, query: str) -> List[str]:
        """
        Простой парсер без LLM (fallback)
        
        Args:
            query: исходный запрос
            
        Returns:
            List[str]: список компонентов
        """
        # Проверяем наличие разделителей
        if ':' not in query and ',' not in query:
            return [query]
        
        print("📝 Используется простой парсер (без LLM)")
        components = []
        
        # Извлекаем размер если есть
        size_match = re.search(r'(\d+x\d+)', query, re.IGNORECASE)
        size = size_match.group(1) if size_match else None
        
        # Разбиваем по двоеточию
        if ':' in query:
            _, after_colon = query.split(':', 1)
            parts = after_colon.split(',')
        else:
            parts = query.split(',')
        
        for part in parts:
            part = part.strip()
            if not part or len(part) < 2:
                continue
            
            # Для основных элементов добавляем размер
            if size and any(word in part.lower() for word in ['короб', 'лоток']):
                if size not in part:
                    part = f"{part} {size}"
            
            # Для крышек не добавляем размер 200x200, только ширину
            if size and 'крышка' in part.lower():
                if size not in part:
                    width = size.split('x')[0]  # Берем только ширину (200)
                    part = f"{part} {width}"
            
            # Для крепежа заменяем размер на стандартное обозначение
            if any(word in part.lower() for word in ['винт', 'гайка', 'болт']):
                # Убираем большие размеры
                part = re.sub(r'\d+x\d+', '', part).strip()
                # Добавляем М6 если нет обозначения
                if not re.search(r'М\d+', part, re.IGNORECASE):
                    part = f"{part} М6"
            
            components.append(part)
        
        return components if components else [query]
