"""
Модуль для работы с LLM (Qwen) для генерации ответов
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict, Optional
import json
import re


class LLMGenerator:
    """Класс для генерации ответов с помощью Qwen LLM"""
    
    def __init__(
        self,
        model_path: str = "./Qwen/Qwen3-4B-Instruct-2507",
        device: str = None
    ):
        """
        Инициализация LLM
        
        Args:
            model_path: путь к модели Qwen
            device: устройство (cuda/cpu/mps)
        """
        self.model_path = model_path
        
        # Определяем устройство
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device
        
        print(f"Загрузка модели с {model_path} на {self.device}...")
        
        # Загружаем токенайзер и модель
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            device_map="auto" if self.device != "cpu" else None,
            trust_remote_code=True
        )
        
        if self.device == "cpu":
            self.model = self.model.to(self.device)
        
        self.model.eval()
        print("Модель загружена успешно!")
    
    def create_prompt(
        self,
        query: str,
        candidates: List[Dict],
        max_candidates: int = 10
    ) -> str:
        """
        Создает промпт для LLM
        
        Args:
            query: запрос пользователя
            candidates: список кандидатов из векторного поиска
            max_candidates: максимальное количество кандидатов
            
        Returns:
            str: промпт для модели
        """
        # Ограничиваем количество кандидатов
        candidates = candidates[:max_candidates]
        
        # Формируем список товаров
        products_text = ""
        for i, item in enumerate(candidates, 1):
            name = item.get('name', '')
            price = item.get('price', 0)
            category = item.get('category', '')
            products_text += f"{i}. {name}\n   Категория: {category}\n   Цена: {price} руб.\n\n"
        
        prompt = f"""Ты - ассистент для поиска строительных материалов и комплектующих.

Запрос пользователя: "{query}"

Доступные товары:
{products_text}

Задача:
1. Проанализируй запрос пользователя
2. Выбери из списка ТОЛЬКО те товары, которые точно соответствуют запросу
3. Если запрос о комплекте (например, "комплект для монтажа"), выбери все необходимые компоненты
4. Верни номера выбранных товаров (от 1 до {len(candidates)}) через запятую

Ответ должен содержать ТОЛЬКО номера товаров, например: 1, 3, 5
Если подходящих товаров нет, верни: 0

Номера выбранных товаров:"""
        
        return prompt
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 100,
        temperature: float = 0.1
    ) -> str:
        """
        Генерирует ответ от LLM
        
        Args:
            prompt: промпт для модели
            max_new_tokens: максимальное количество токенов
            temperature: температура генерации
            
        Returns:
            str: сгенерированный текст
        """
        # Токенизация
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096
        ).to(self.device)
        
        # Генерация
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Декодирование
        generated_text = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return generated_text.strip()
    
    def extract_selected_indices(self, llm_response: str) -> List[int]:
        """
        Извлекает номера выбранных товаров из ответа LLM
        
        Args:
            llm_response: ответ от LLM
            
        Returns:
            List[int]: список индексов (начиная с 1)
        """
        # Ищем все числа в ответе
        numbers = re.findall(r'\d+', llm_response)
        
        if not numbers:
            return []
        
        # Преобразуем в int и фильтруем 0
        indices = [int(n) for n in numbers if int(n) > 0]
        
        return indices
    
    def select_products(
        self,
        query: str,
        candidates: List[Dict],
        max_candidates: int = 10
    ) -> List[Dict]:
        """
        Выбирает подходящие товары с помощью LLM
        
        Args:
            query: запрос пользователя
            candidates: список кандидатов
            max_candidates: максимальное количество кандидатов
            
        Returns:
            List[Dict]: выбранные товары
        """
        if not candidates:
            return []
        
        # Создаем промпт
        prompt = self.create_prompt(query, candidates, max_candidates)
        
        # Генерируем ответ
        llm_response = self.generate(prompt)
        
        # Извлекаем индексы
        selected_indices = self.extract_selected_indices(llm_response)
        
        # Получаем выбранные товары (индексы начинаются с 1)
        selected_products = []
        for idx in selected_indices:
            if 1 <= idx <= len(candidates):
                selected_products.append(candidates[idx - 1])
        
        return selected_products


if __name__ == "__main__":
    # Тестирование (требует загруженной модели)
    print("Тестирование LLM Generator...")
    
    # Тестовые данные
    test_candidates = [
        {
            "name": "Короб 200x200 мм, L=2000 мм, горячее цинкование",
            "price": 88498,
            "category": "Короб"
        },
        {
            "name": "Крышка 200 мм, L=2000 мм, горячее цинкование",
            "price": 45131,
            "category": "Крышка"
        },
        {
            "name": "Винт с крестообразным шлицем М6х10",
            "price": 12534,
            "category": "Винт"
        },
        {
            "name": "Гайка с насечкой М6",
            "price": 38194,
            "category": "Гайка"
        }
    ]
    
    # Создаем промпт без загрузки модели
    generator = LLMGenerator.__new__(LLMGenerator)
    prompt = generator.create_prompt(
        "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки",
        test_candidates
    )
    
    print("\nПример промпта:")
    print("="*60)
    print(prompt)
    print("="*60)
    
    # Тест извлечения индексов
    test_response = "1, 2, 3, 4"
    indices = generator.extract_selected_indices(test_response)
    print(f"\nТестовый ответ: {test_response}")
    print(f"Извлеченные индексы: {indices}")
