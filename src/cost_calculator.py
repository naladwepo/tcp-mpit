"""
Утилиты для расчета стоимости и форматирования цен
"""

import re
from typing import List, Dict


def parse_price(price_str: str) -> float:
    """
    Извлекает числовое значение цены из строки
    
    Args:
        price_str: строка с ценой
        
    Returns:
        float: числовое значение цены
    """
    if isinstance(price_str, (int, float)):
        return float(price_str)
    
    price_str = str(price_str).replace(' ', '').replace('руб.', '').replace('руб', '')
    price_str = price_str.replace(',', '.')
    
    match = re.search(r'(\d+(?:\.\d+)?)', price_str)
    if match:
        return float(match.group(1))
    return 0.0


def format_price(price: float) -> str:
    """
    Форматирует цену для отображения
    
    Args:
        price: числовое значение цены
        
    Returns:
        str: отформатированная цена
    """
    # Округляем до целых
    price_int = int(round(price))
    
    # Добавляем разделители тысяч
    price_str = f"{price_int:,}".replace(',', ' ')
    
    return f"{price_str} руб."


def calculate_total_cost(items: List[Dict]) -> float:
    """
    Рассчитывает общую стоимость списка товаров
    
    Args:
        items: список словарей с товарами (должны содержать поле 'price')
        
    Returns:
        float: общая стоимость
    """
    total = 0.0
    for item in items:
        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        
        if isinstance(price, str):
            price = parse_price(price)
        
        total += float(price) * float(quantity)
    
    return total


def format_item_for_response(item: Dict) -> Dict:
    """
    Форматирует товар для JSON ответа
    
    Args:
        item: словарь с данными о товаре
        
    Returns:
        Dict: отформатированный словарь
    """
    name = item.get('name', '')
    price = item.get('price', 0)
    
    return {
        "name": name,
        "cost": format_price(price)
    }


def create_response_json(
    found_items: List[Dict],
    query_id: int = None,
    complexity: str = None
) -> Dict:
    """
    Создает JSON ответ в формате как в примерах
    
    Args:
        found_items: список найденных товаров
        query_id: ID запроса
        complexity: сложность запроса
        
    Returns:
        Dict: структурированный ответ
    """
    formatted_items = [format_item_for_response(item) for item in found_items]
    total_cost = calculate_total_cost(found_items)
    
    response = {
        "found_items": formatted_items,
        "items_count": len(formatted_items),
        "total_cost": format_price(total_cost)
    }
    
    result = {"response": response}
    
    if query_id is not None:
        result["id"] = query_id
    
    if complexity is not None:
        result["complexity"] = complexity
    
    return result


if __name__ == "__main__":
    # Тестирование
    test_items = [
        {"name": "Короб 100x100", "price": 61263},
        {"name": "Гайка М6", "price": "38194 руб."},
        {"name": "Крышка 200 мм", "price": 45131}
    ]
    
    print("Тестовые товары:")
    for item in test_items:
        print(f"  - {item['name']}: {item['price']}")
    
    total = calculate_total_cost(test_items)
    print(f"\nОбщая стоимость: {format_price(total)}")
    
    response = create_response_json(test_items, query_id=1, complexity="simple")
    print("\nJSON ответ:")
    import json
    print(json.dumps(response, ensure_ascii=False, indent=2))
