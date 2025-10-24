"""
Модуль для разбиения сложных запросов на компоненты
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class QueryComponent:
    """Компонент запроса"""
    text: str
    weight: float = 1.0
    category: str = None


class QueryDecomposer:
    """Разбивает сложные запросы на отдельные компоненты"""
    
    # Ключевые слова для разделения
    SEPARATORS = [
        ':', ',', ';', 
        ' и ', ' или ',
        'включая', 'в том числе',
        'с комплектом', 'комплект'
    ]
    
    # Паттерны для извлечения компонентов
    PATTERNS = {
        'размер': r'(\d+x\d+|\d+\s*мм)',
        'длина': r'L\s*=\s*\d+|длин[ау]\s+\d+',
        'диаметр': r'[ØД]\s*\d+|М\d+',
        'материал': r'(оцинкован|нержавеющ|сталь)',
    }
    
    def __init__(self):
        pass
    
    def decompose(self, query: str) -> List[QueryComponent]:
        """
        Разбивает запрос на компоненты
        
        Args:
            query: исходный запрос
            
        Returns:
            List[QueryComponent]: список компонентов запроса
        """
        components = []
        
        # Проверяем, является ли запрос составным
        if not self._is_complex_query(query):
            # Простой запрос - возвращаем как есть
            return [QueryComponent(text=query, weight=1.0)]
        
        # Извлекаем размеры из основного запроса
        size_match = re.search(r'(\d+x\d+)', query, re.IGNORECASE)
        size_context = size_match.group(1) if size_match else None
        
        # Разбиваем по разделителям
        parts = self._split_query(query)
        
        for part in parts:
            part = part.strip()
            if not part or len(part) < 3:
                continue
            
            # Добавляем контекст размера если нужно
            if size_context and size_context not in part:
                # Если это не основное описание, добавляем размер
                if not re.search(r'комплект|набор|для монтажа', part, re.IGNORECASE):
                    part = f"{part} {size_context}"
            
            components.append(QueryComponent(
                text=part,
                weight=1.0
            ))
        
        return components if components else [QueryComponent(text=query, weight=1.0)]
    
    def _is_complex_query(self, query: str) -> bool:
        """Проверяет, является ли запрос составным"""
        # Ищем разделители
        for sep in self.SEPARATORS:
            if sep in query.lower():
                return True
        
        # Ищем перечисления
        if query.count(',') >= 2:
            return True
        
        return False
    
    def _split_query(self, query: str) -> List[str]:
        """Разбивает запрос на части"""
        parts = []
        
        # Сначала делим по двоеточию
        if ':' in query:
            before_colon, after_colon = query.split(':', 1)
            # Разбиваем часть после двоеточия по запятым
            items = after_colon.split(',')
            parts.extend([item.strip() for item in items if item.strip()])
        else:
            # Просто делим по запятым
            items = query.split(',')
            parts.extend([item.strip() for item in items if item.strip()])
        
        # Дополнительно разбиваем по " и "
        expanded_parts = []
        for part in parts:
            if ' и ' in part.lower():
                sub_parts = re.split(r'\s+и\s+', part, flags=re.IGNORECASE)
                expanded_parts.extend(sub_parts)
            else:
                expanded_parts.append(part)
        
        return expanded_parts
