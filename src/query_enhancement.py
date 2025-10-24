"""
Улучшение запросов пользователей для более точного поиска
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class QueryIntent:
    """Намерение пользователя в запросе"""
    intent_type: str  # 'single_item', 'multi_item', 'assembly', 'specification'
    items: List[str]  # Список товаров для поиска
    constraints: Dict[str, str]  # Ограничения (размер, материал, цвет и т.д.)
    original_query: str


class QueryEnhancer:
    """
    Улучшает запросы пользователей для более точного поиска товаров
    """
    
    # Словари для нормализации терминов
    PRODUCT_SYNONYMS = {
        'короб': ['короб', 'корпус', 'бокс', 'ящик'],
        'лоток': ['лоток', 'канал', 'кабель-канал', 'лотки'],
        'крышка': ['крышка', 'заглушка', 'закрытие'],
        'гайка': ['гайка', 'гайки'],
        'винт': ['винт', 'винты', 'болт', 'болты', 'шуруп'],
        'кабель': ['кабель', 'провод', 'проводка'],
        'труба': ['труба', 'трубка', 'трубопровод'],
    }
    
    # Стандартные размеры крепежа
    FASTENER_SIZES = {
        'малый': 'М4',
        'средний': 'М6',
        'большой': 'М8',
        'крупный': 'М10',
    }
    
    # Размеры коробов и лотков (стандартные)
    STANDARD_SIZES = [
        '50', '75', '100', '150', '200', '300', '400', '600'
    ]
    
    def __init__(self):
        """Инициализация"""
        pass
    
    def analyze_intent(self, query: str) -> QueryIntent:
        """
        Анализирует намерение пользователя
        
        Args:
            query: исходный запрос
            
        Returns:
            QueryIntent: распознанное намерение с компонентами
        """
        query_lower = query.lower()
        
        # Извлекаем ограничения (размер, материал, цвет)
        constraints = self._extract_constraints(query)
        
        # Определяем тип запроса
        if self._is_assembly_query(query_lower):
            # Комплект/набор товаров
            items = self._extract_assembly_items(query, constraints)
            return QueryIntent(
                intent_type='assembly',
                items=items,
                constraints=constraints,
                original_query=query
            )
        
        elif self._is_multi_item_query(query_lower):
            # Несколько товаров через запятую
            items = self._extract_multi_items(query, constraints)
            return QueryIntent(
                intent_type='multi_item',
                items=items,
                constraints=constraints,
                original_query=query
            )
        
        elif self._is_specification_query(query_lower):
            # Конкретная спецификация товара
            items = self._extract_specification(query, constraints)
            return QueryIntent(
                intent_type='specification',
                items=items,
                constraints=constraints,
                original_query=query
            )
        
        else:
            # Простой запрос одного товара
            items = [self._enhance_single_query(query, constraints)]
            return QueryIntent(
                intent_type='single_item',
                items=items,
                constraints=constraints,
                original_query=query
            )
    
    def _is_assembly_query(self, query: str) -> bool:
        """Проверяет, является ли запрос о комплекте/наборе"""
        assembly_keywords = [
            'комплект', 'набор', 'монтаж', 'установка',
            'вместе', 'с креплением', 'со всем необходимым'
        ]
        return any(kw in query for kw in assembly_keywords)
    
    def _is_multi_item_query(self, query: str) -> bool:
        """Проверяет, является ли запрос о нескольких товарах"""
        return ',' in query or ' и ' in query or ' + ' in query or ' плюс ' in query
    
    def _is_specification_query(self, query: str) -> bool:
        """Проверяет, является ли запрос с конкретной спецификацией"""
        spec_patterns = [
            r'\d+x\d+',  # размер 200x200
            r'М\d+',     # резьба М6
            r'\d+\s*мм', # 600 мм
            r'IP\d+',    # степень защиты IP67
        ]
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in spec_patterns)
    
    def _extract_constraints(self, query: str) -> Dict[str, str]:
        """
        Извлекает ограничения из запроса
        
        Returns:
            Dict с ключами: size, material, color, protection_class и др.
        """
        constraints = {}
        
        # Размер (200x200, 600 мм и т.д.)
        size_match = re.search(r'(\d+x\d+)', query)
        if size_match:
            constraints['size_2d'] = size_match.group(1)
            # Извлекаем ширину/высоту отдельно
            parts = size_match.group(1).split('x')
            constraints['width'] = parts[0]
            if len(parts) > 1:
                constraints['height'] = parts[1]
        
        # Линейный размер (600 мм, 2 метра)
        linear_match = re.search(r'(\d+)\s*(мм|см|м)', query, re.IGNORECASE)
        if linear_match:
            value, unit = linear_match.groups()
            # Нормализуем к мм
            if unit.lower() == 'см':
                value = str(int(value) * 10)
            elif unit.lower() == 'м':
                value = str(int(value) * 1000)
            constraints['length'] = value
        
        # Резьба (М6, М8, М10)
        thread_match = re.search(r'М(\d+)', query, re.IGNORECASE)
        if thread_match:
            constraints['thread'] = f"М{thread_match.group(1)}"
        
        # Степень защиты (IP67, IP54)
        ip_match = re.search(r'IP(\d+)', query, re.IGNORECASE)
        if ip_match:
            constraints['ip_rating'] = f"IP{ip_match.group(1)}"
        
        # Материал
        materials = {
            'металл': ['металл', 'стальн', 'оцинк'],
            'пластик': ['пластик', 'пвх', 'полимер'],
            'нержавейка': ['нержавейка', 'нержавеющ'],
        }
        for material, keywords in materials.items():
            if any(kw in query.lower() for kw in keywords):
                constraints['material'] = material
                break
        
        # Тип монтажа
        if 'настенн' in query.lower() or 'на стену' in query.lower():
            constraints['mounting'] = 'настенный'
        elif 'потолочн' in query.lower() or 'на потолок' in query.lower():
            constraints['mounting'] = 'потолочный'
        elif 'наполь' in query.lower() or 'на пол' in query.lower():
            constraints['mounting'] = 'напольный'
        
        # Тип (перфорированный, глухой, прозрачный)
        if 'перфорир' in query.lower():
            constraints['type'] = 'перфорированный'
        elif 'глух' in query.lower():
            constraints['type'] = 'глухой'
        elif 'прозрачн' in query.lower():
            constraints['type'] = 'прозрачный'
        
        return constraints
    
    def _extract_assembly_items(self, query: str, constraints: Dict[str, str]) -> List[str]:
        """
        Извлекает компоненты из запроса о комплекте
        
        Пример: "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки"
        """
        items = []
        
        # Разбиваем по двоеточию
        if ':' in query:
            main_part, items_part = query.split(':', 1)
        else:
            main_part = query
            items_part = query
        
        # Извлекаем основной объект из первой части (короб, лоток и т.д.)
        main_object = self._extract_main_object(main_part)
        
        # Разбиваем список на компоненты
        components = re.split(r'[,;]|\bи\b|\bплюс\b|\+', items_part)
        
        for comp in components:
            comp = comp.strip()
            if not comp or len(comp) < 2:
                continue
            
            comp_lower = comp.lower()
            
            # Для основного товара (короб, лоток) - добавляем полный размер
            if any(word in comp_lower for word in ['короб', 'лоток', 'корпус']):
                enhanced = self._enhance_main_item(comp, constraints)
                items.append(enhanced)
            
            # Для крышки - только ширина
            elif 'крышка' in comp_lower:
                enhanced = self._enhance_cover(comp, constraints)
                items.append(enhanced)
            
            # Для крепежа (винты, гайки) - стандартное обозначение
            elif any(word in comp_lower for word in ['винт', 'гайка', 'болт', 'шуруп', 'крепеж']):
                enhanced = self._enhance_fastener(comp, constraints)
                items.append(enhanced)
            
            # Остальные товары - как есть с ограничениями
            else:
                enhanced = self._apply_constraints(comp, constraints)
                items.append(enhanced)
        
        return items if items else [query]
    
    def _extract_multi_items(self, query: str, constraints: Dict[str, str]) -> List[str]:
        """
        Извлекает компоненты из запроса с несколькими товарами
        
        Пример: "Гайка М6, винт М6, шайба"
        """
        items = []
        
        # Разбиваем по разделителям
        components = re.split(r'[,;]|\bи\b|\bплюс\b|\+', query)
        
        for comp in components:
            comp = comp.strip()
            if not comp or len(comp) < 2:
                continue
            
            enhanced = self._enhance_single_query(comp, constraints)
            items.append(enhanced)
        
        return items
    
    def _extract_specification(self, query: str, constraints: Dict[str, str]) -> List[str]:
        """
        Обрабатывает запрос с конкретной спецификацией
        
        Пример: "Лоток перфорированный 600 мм IP67"
        """
        enhanced = self._enhance_single_query(query, constraints)
        return [enhanced]
    
    def _enhance_single_query(self, query: str, constraints: Dict[str, str]) -> str:
        """
        Улучшает простой запрос одного товара
        """
        query_lower = query.lower()
        
        # Определяем тип товара
        if any(word in query_lower for word in ['короб', 'корпус', 'бокс']):
            return self._enhance_main_item(query, constraints)
        
        elif 'крышка' in query_lower:
            return self._enhance_cover(query, constraints)
        
        elif any(word in query_lower for word in ['винт', 'гайка', 'болт', 'шуруп']):
            return self._enhance_fastener(query, constraints)
        
        elif 'лоток' in query_lower:
            return self._enhance_tray(query, constraints)
        
        else:
            return self._apply_constraints(query, constraints)
    
    def _enhance_main_item(self, item: str, constraints: Dict[str, str]) -> str:
        """
        Улучшает запрос основного товара (короб, лоток)
        
        Добавляет: полный размер, тип монтажа, степень защиты
        """
        result = item.strip()
        
        # Добавляем размер если есть
        if 'size_2d' in constraints and constraints['size_2d'] not in result:
            result = f"{result} {constraints['size_2d']}"
        elif 'width' in constraints and 'x' not in result:
            result = f"{result} {constraints['width']}"
        
        # Добавляем тип монтажа если нет в запросе
        if 'mounting' in constraints and constraints['mounting'] not in result.lower():
            result = f"{result} {constraints['mounting']}"
        
        # Добавляем степень защиты
        if 'ip_rating' in constraints and 'ip' not in result.lower():
            result = f"{result} {constraints['ip_rating']}"
        
        return result
    
    def _enhance_cover(self, item: str, constraints: Dict[str, str]) -> str:
        """
        Улучшает запрос крышки
        
        Для крышек используем только ШИРИНУ, а не полный размер
        """
        result = item.strip()
        
        # Для крышек берем только ширину (первое число из 200x200)
        if 'width' in constraints:
            width = constraints['width']
            if width not in result:
                result = f"{result} {width}"
        
        # Добавляем тип если указан
        if 'type' in constraints and constraints['type'] not in result.lower():
            result = f"{result} {constraints['type']}"
        
        return result
    
    def _enhance_fastener(self, item: str, constraints: Dict[str, str]) -> str:
        """
        Улучшает запрос крепежа (винты, гайки)
        
        Стандартизирует обозначение резьбы (М6, М8)
        """
        result = item.strip()
        
        # Убираем большие размеры типа 200x200
        result = re.sub(r'\d+x\d+', '', result).strip()
        
        # Проверяем наличие резьбы в самом запросе
        existing_thread = re.search(r'М\d+', result, re.IGNORECASE)
        
        if existing_thread:
            # Резьба уже есть - оставляем как есть (но нормализуем название)
            thread_value = existing_thread.group(0)
            normalized = result.lower()
            
            if 'винт' in normalized or 'болт' in normalized:
                base = 'Винт'
            elif 'гайк' in normalized:
                base = 'Гайка'
            elif 'шайб' in normalized:
                base = 'Шайба'
            elif 'крепеж' in normalized or 'крепл' in normalized:
                base = 'Винт'  # Крепеж обычно = винты
            else:
                return result
            
            return f"{base} {thread_value}"
        
        # Нормализуем название (винт/винты/болт -> винт)
        normalized = result.lower()
        
        if 'винт' in normalized or 'болт' in normalized:
            base = 'Винт'
        elif 'гайк' in normalized:
            base = 'Гайка'
        elif 'шайб' in normalized:
            base = 'Шайба'
        elif 'крепеж' in normalized or 'крепл' in normalized:
            base = 'Винт'  # Крепеж обычно = винты
        else:
            base = result
        
        # Добавляем резьбу если есть в ограничениях
        if 'thread' in constraints:
            thread = constraints['thread']
            result = f"{base} {thread}"
        else:
            # Если резьба не указана, используем стандартную М6
            result = f"{base} М6"
        
        return result
    
    def _enhance_tray(self, item: str, constraints: Dict[str, str]) -> str:
        """
        Улучшает запрос лотка
        
        Добавляет: размер, тип (перфорированный/глухой)
        """
        result = item.strip()
        
        # Добавляем длину/ширину
        if 'length' in constraints and constraints['length'] not in result:
            result = f"{result} {constraints['length']}"
        elif 'width' in constraints and constraints['width'] not in result:
            result = f"{result} {constraints['width']}"
        
        # Добавляем тип
        if 'type' in constraints and constraints['type'] not in result.lower():
            result = f"{result} {constraints['type']}"
        
        return result
    
    def _apply_constraints(self, item: str, constraints: Dict[str, str]) -> str:
        """
        Применяет общие ограничения к товару
        """
        result = item.strip()
        
        # Добавляем материал если указан
        if 'material' in constraints and constraints['material'] not in result.lower():
            result = f"{result} {constraints['material']}"
        
        return result
    
    def _extract_main_object(self, text: str) -> Optional[str]:
        """Извлекает основной объект из текста"""
        text_lower = text.lower()
        
        for product_type in ['короб', 'лоток', 'корпус', 'бокс', 'ящик']:
            if product_type in text_lower:
                return product_type
        
        return None
    
    def enhance_query(self, query: str) -> List[str]:
        """
        Главный метод: улучшает запрос и возвращает список улучшенных подзапросов
        
        Args:
            query: исходный запрос пользователя
            
        Returns:
            List[str]: список улучшенных запросов для поиска
        """
        intent = self.analyze_intent(query)
        
        print(f"🎯 Тип запроса: {intent.intent_type}")
        print(f"📋 Найдено компонентов: {len(intent.items)}")
        
        if intent.constraints:
            print(f"🔍 Ограничения: {intent.constraints}")
        
        for i, item in enumerate(intent.items, 1):
            print(f"  {i}. {item}")
        
        return intent.items


# Пример использования
if __name__ == "__main__":
    enhancer = QueryEnhancer()
    
    test_queries = [
        "Гайка М6",
        "Короб 200x200",
        "Комплект для монтажа короба 200x200: короб, крышка, винты и гайки",
        "Лоток перфорированный 600 мм",
        "Короб настенный IP67 300x400, крышка и крепеж",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Запрос: {query}")
        print('='*60)
        enhanced = enhancer.enhance_query(query)
        print()
