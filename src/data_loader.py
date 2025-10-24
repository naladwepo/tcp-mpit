"""
Модуль для загрузки и обработки данных из CSV файлов
"""

import pandas as pd
import re
from typing import List, Dict, Optional
from pathlib import Path


class DataLoader:
    """Класс для загрузки и preprocessing данных о товарах"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.products_df = None
        
    def parse_price(self, price_str: str) -> float:
        """
        Извлекает числовое значение цены из строки
        
        Args:
            price_str: строка с ценой (например, "61263 руб." или "61263")
            
        Returns:
            float: числовое значение цены
        """
        if pd.isna(price_str):
            return 0.0
            
        # Удаляем все нечисловые символы кроме точки и запятой
        price_str = str(price_str).replace(' ', '').replace('руб.', '').replace('руб', '')
        price_str = price_str.replace(',', '.')
        
        # Извлекаем первое число
        match = re.search(r'(\d+(?:\.\d+)?)', price_str)
        if match:
            return float(match.group(1))
        return 0.0
    
    def clean_product_name(self, name: str) -> str:
        """
        Очищает название товара от лишней информации о цене
        
        Args:
            name: исходное название товара
            
        Returns:
            str: очищенное название
        """
        if pd.isna(name):
            return ""
        
        # Удаляем цену в конце строки (например, "- 61263 руб.")
        name = re.sub(r'\s*-\s*\d+\s*руб\.?\s*$', '', str(name))
        return name.strip()
    
    def load_changed_csv(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Загружает данные из changed_50.csv
        
        Args:
            filepath: путь к файлу (если None, использует стандартный путь)
            
        Returns:
            DataFrame с колонками: name, price, category
        """
        if filepath is None:
            filepath = self.data_dir / "changed_50.csv"
        
        df = pd.read_csv(filepath, encoding='utf-8')
        
        # Переименовываем колонки для единообразия
        df = df.rename(columns={
            'Товар': 'name',
            'Цена': 'price',
            'Категория': 'category'
        })
        
        # Очищаем названия и парсим цены
        df['name'] = df['name'].apply(self.clean_product_name)
        df['price'] = df['price'].apply(self.parse_price)
        
        return df
    
    def load_materials_csv(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Загружает данные из materials_50_items.csv
        
        Args:
            filepath: путь к файлу (если None, использует стандартный путь)
            
        Returns:
            DataFrame с колонками: name, price
        """
        if filepath is None:
            filepath = self.data_dir / "materials_50_items.csv"
        
        # Читаем построчно для обработки нестандартного формата
        rows = []
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_name = ""
        for i, line in enumerate(lines):
            if i == 0:  # Пропускаем заголовок
                continue
            
            line = line.strip()
            if not line:
                continue
            
            # Если строка начинается с кавычки, это начало записи
            if line.startswith('"'):
                # Извлекаем всё содержимое между кавычками
                parts = line.split('",')
                if len(parts) == 2:
                    # Название и цена в одной строке
                    name_part = parts[0].strip('"')
                    price_part = parts[1].strip()
                    
                    # Разделяем название и цену внутри name_part (они через запятую)
                    if ',' in name_part:
                        name_price_split = name_part.rsplit(',', 1)
                        if len(name_price_split) == 2:
                            name = name_price_split[0].strip()
                            price = name_price_split[1].strip()
                        else:
                            name = name_part
                            price = price_part
                    else:
                        name = name_part
                        price = price_part
                    
                    rows.append({'name': name, 'price': price})
            else:
                # Строка без кавычек - простой формат через запятую
                parts = line.rsplit(',', 1)
                if len(parts) == 2:
                    rows.append({'name': parts[0].strip(), 'price': parts[1].strip()})
        
        df = pd.DataFrame(rows)
        
        # Парсим цены
        df['price'] = df['price'].apply(self.parse_price)
        
        # Очищаем названия
        df['name'] = df['name'].apply(lambda x: str(x).strip() if not pd.isna(x) else "")
        
        # Извлекаем категорию из названия (первое слово)
        df['category'] = df['name'].apply(lambda x: x.split()[0] if x else "Неизвестно")
        
        return df
    
    def combine_datasets(self) -> pd.DataFrame:
        """
        Объединяет данные из обоих CSV файлов
        
        Returns:
            DataFrame с объединенными данными
        """
        df1 = self.load_changed_csv()
        df2 = self.load_materials_csv()
        
        # Объединяем датасеты
        combined = pd.concat([df1, df2], ignore_index=True)
        
        # Удаляем дубликаты по названию
        combined = combined.drop_duplicates(subset=['name'], keep='first')
        
        # Добавляем ID для каждого товара
        combined['id'] = range(len(combined))
        
        # Убираем пустые названия
        combined = combined[combined['name'].str.len() > 0]
        
        # Переименовываем 'price' в 'cost' для совместимости с LLMValidator
        if 'price' in combined.columns:
            combined = combined.rename(columns={'price': 'cost'})
        
        self.products_df = combined
        return combined
    
    def get_products(self) -> pd.DataFrame:
        """
        Возвращает загруженные данные о товарах
        
        Returns:
            DataFrame с товарами
        """
        if self.products_df is None:
            return self.combine_datasets()
        return self.products_df
    
    def load_all_products(self) -> List[Dict]:
        """
        Загружает все товары в виде списка словарей
        
        Returns:
            List[Dict]: список словарей с товарами
        """
        df = self.get_products()
        return df.to_dict('records')
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        Получает товар по ID
        
        Args:
            product_id: ID товара
            
        Returns:
            Dict с данными товара или None
        """
        if self.products_df is None:
            self.combine_datasets()
        
        product = self.products_df[self.products_df['id'] == product_id]
        if len(product) > 0:
            return product.iloc[0].to_dict()
        return None
    
    def search_by_category(self, category: str) -> List[Dict]:
        """
        Поиск товаров по категории
        
        Args:
            category: название категории
            
        Returns:
            List словарей с товарами
        """
        if self.products_df is None:
            self.combine_datasets()
        
        # Поиск с игнорированием регистра
        mask = self.products_df['category'].str.contains(category, case=False, na=False)
        results = self.products_df[mask]
        
        return results.to_dict('records')


if __name__ == "__main__":
    # Тестирование модуля
    loader = DataLoader()
    df = loader.combine_datasets()
    
    print(f"Загружено товаров: {len(df)}")
    print(f"\nПервые 5 товаров:")
    print(df[['id', 'name', 'price', 'category']].head())
    
    print(f"\nКатегории:")
    print(df['category'].value_counts().head(10))
