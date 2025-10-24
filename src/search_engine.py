"""
Модуль векторного поиска с использованием FAISS и sentence-transformers
"""

import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd


class VectorSearchEngine:
    """Класс для векторного поиска товаров"""
    
    def __init__(
        self, 
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_dir: str = "data/index",
        device: str = "cpu"
    ):
        """
        Инициализация поискового движка
        
        Args:
            model_name: название модели для создания эмбеддингов
                По умолчанию: all-MiniLM-L6-v2 (стабильная, быстрая модель)
            index_dir: директория для сохранения индекса
            device: устройство для вычислений (cpu/cuda/mps)
        """
        self.model_name = model_name
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        
        # Отложенная загрузка модели
        self.model = None
        self.dimension = None
        self.index = None
        self.products = None
        self.product_embeddings = None
        
        print(f"Инициализация векторного поиска (модель: {model_name})...")
        
    def _load_model(self):
        """Загружает модель при первом использовании"""
        if self.model is not None:
            return
        
        try:
            print(f"Загрузка модели {self.model_name}...")
            
            # Импортируем только когда нужно
            import torch
            from sentence_transformers import SentenceTransformer
            
            # Принудительно используем CPU
            torch.set_num_threads(1)
            
            # Загружаем модель с явным указанием устройства
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device
            )
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            print(f"✓ Модель загружена (размерность: {self.dimension})")
            
        except Exception as e:
            print(f"⚠ Не удалось загрузить модель: {e}")
            raise RuntimeError(
                "Не удалось загрузить векторную модель. "
                "Используйте SimpleSearchEngine или исправьте torch установку."
            )
        
    def create_search_text(self, product: Dict) -> str:
        """
        Создает текст для поиска из данных товара
        
        Args:
            product: словарь с данными о товаре
            
        Returns:
            str: форматированный текст для эмбеддинга
        """
        name = product.get('name', '')
        category = product.get('category', '')
        
        # Комбинируем название и категорию для лучшего поиска
        search_text = f"{category}: {name}"
        return search_text
    
    def build_index(self, products_df: pd.DataFrame, force_rebuild: bool = False):
        """
        Создает векторный индекс для товаров
        
        Args:
            products_df: DataFrame с товарами
            force_rebuild: принудительно пересоздать индекс
        """
        # Загружаем модель если еще не загружена
        self._load_model()
        
        # Импортируем FAISS и tqdm
        import faiss
        from tqdm import tqdm
        
        index_path = self.index_dir / "faiss.index"
        products_path = self.index_dir / "products.pkl"
        embeddings_path = self.index_dir / "embeddings.npy"
        
        # Проверяем существование индекса
        if not force_rebuild and index_path.exists() and products_path.exists():
            print("Загрузка существующего индекса...")
            self.load_index()
            return
        
        print("Создание нового индекса...")
        self.products = products_df.to_dict('records')
        
        # Создаем тексты для эмбеддинга
        texts = [self.create_search_text(p) for p in self.products]
        
        # Генерируем эмбеддинги с прогресс-баром
        print("Генерация эмбеддингов...")
        self.product_embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,  # Нормализация для cosine similarity
            device=self.device
        )
        
        # Создаем FAISS индекс
        print("Создание FAISS индекса...")
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (для нормализованных векторов = cosine)
        self.index.add(self.product_embeddings)
        
        # Сохраняем индекс
        print("Сохранение индекса...")
        faiss.write_index(self.index, str(index_path))
        
        with open(products_path, 'wb') as f:
            pickle.dump(self.products, f)
        
        np.save(embeddings_path, self.product_embeddings)
        
        print(f"Индекс создан для {len(self.products)} товаров")
    
    def load_index(self):
        """Загружает существующий индекс"""
        import faiss
        
        index_path = self.index_dir / "faiss.index"
        products_path = self.index_dir / "products.pkl"
        embeddings_path = self.index_dir / "embeddings.npy"
        
        if not index_path.exists():
            raise FileNotFoundError(f"Индекс не найден в {index_path}")
        
        self.index = faiss.read_index(str(index_path))
        
        with open(products_path, 'rb') as f:
            self.products = pickle.load(f)
        
        if embeddings_path.exists():
            self.product_embeddings = np.load(embeddings_path)
        
        print(f"Индекс загружен: {len(self.products)} товаров")
    
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[Tuple[Dict, float]]:
        """
        Выполняет поиск по запросу
        
        Args:
            query: поисковый запрос
            top_k: количество результатов
            score_threshold: минимальный порог релевантности (0-1)
            
        Returns:
            List кортежей (товар, релевантность)
        """
        # Загружаем модель если еще не загружена
        if self.model is None:
            self._load_model()
        
        if self.index is None:
            raise ValueError("Индекс не создан. Вызовите build_index() или load_index()")
        
        # Создаем эмбеддинг запроса
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            device=self.device
        )
        
        # Поиск в FAISS
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Формируем результаты
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.products) and score >= score_threshold:
                product = self.products[idx]
                results.append((product, float(score)))
        
        return results
    
    def search_by_category(
        self,
        query: str,
        category: str,
        top_k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """
        Поиск с фильтрацией по категории
        
        Args:
            query: поисковый запрос
            category: фильтр по категории
            top_k: количество результатов
            
        Returns:
            List кортежей (товар, релевантность)
        """
        # Сначала получаем больше результатов
        all_results = self.search(query, top_k=top_k * 3)
        
        # Фильтруем по категории
        filtered = [
            (product, score) 
            for product, score in all_results 
            if category.lower() in product.get('category', '').lower()
        ]
        
        return filtered[:top_k]
    
    def get_similar_products(
        self,
        product_id: int,
        top_k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Находит похожие товары
        
        Args:
            product_id: ID товара
            top_k: количество результатов
            
        Returns:
            List кортежей (товар, релевантность)
        """
        if self.product_embeddings is None:
            raise ValueError("Эмбеддинги не загружены")
        
        # Находим индекс товара
        product_idx = next(
            (i for i, p in enumerate(self.products) if p['id'] == product_id),
            None
        )
        
        if product_idx is None:
            return []
        
        # Получаем эмбеддинг товара
        product_embedding = self.product_embeddings[product_idx:product_idx+1]
        
        # Ищем похожие
        scores, indices = self.index.search(product_embedding, top_k + 1)
        
        # Исключаем сам товар
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != product_idx and idx < len(self.products):
                product = self.products[idx]
                results.append((product, float(score)))
        
        return results[:top_k]


if __name__ == "__main__":
    # Тестирование модуля
    from data_loader import DataLoader
    
    print("Загрузка данных...")
    loader = DataLoader()
    df = loader.combine_datasets()
    
    print("\nСоздание поискового движка...")
    search_engine = VectorSearchEngine(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Меньшая модель для теста
    )
    
    print("\nСоздание индекса...")
    search_engine.build_index(df)
    
    # Тестовые запросы
    test_queries = [
        "Гайка М6",
        "Короб 200x200",
        "Лоток перфорированный"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Запрос: {query}")
        print('='*60)
        
        results = search_engine.search(query, top_k=3)
        
        for i, (product, score) in enumerate(results, 1):
            print(f"\n{i}. {product['name'][:80]}...")
            print(f"   Цена: {product['price']} руб.")
            print(f"   Релевантность: {score:.3f}")
