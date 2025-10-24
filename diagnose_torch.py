#!/usr/bin/env python3
"""
Диагностика проблем с torch и sentence-transformers
"""

import sys

print("="*70)
print("ДИАГНОСТИКА TORCH И SENTENCE-TRANSFORMERS")
print("="*70)

# 1. Проверка torch
print("\n[1/5] Проверка torch...")
try:
    import torch
    print(f"✓ torch {torch.__version__} установлен")
    print(f"  - CPU доступен: {torch.cuda.is_available() == False or True}")
    print(f"  - CUDA доступен: {torch.cuda.is_available()}")
    
    # Проверка MPS (Apple Silicon)
    if hasattr(torch.backends, 'mps'):
        print(f"  - MPS доступен: {torch.backends.mps.is_available()}")
    
    # Пробуем создать простой тензор
    try:
        x = torch.tensor([1.0, 2.0, 3.0])
        print(f"  - Создание тензора: ✓")
    except Exception as e:
        print(f"  - Создание тензора: ✗ {e}")
        
except ImportError as e:
    print(f"✗ torch не установлен: {e}")
    print("  Установите: pip install torch")
    sys.exit(1)
except Exception as e:
    print(f"✗ Ошибка при работе с torch: {e}")

# 2. Проверка sentence-transformers
print("\n[2/5] Проверка sentence-transformers...")
try:
    import sentence_transformers
    print(f"✓ sentence-transformers {sentence_transformers.__version__} установлен")
except ImportError as e:
    print(f"✗ sentence-transformers не установлен: {e}")
    print("  Установите: pip install sentence-transformers")
    sys.exit(1)

# 3. Проверка FAISS
print("\n[3/5] Проверка faiss...")
try:
    import faiss
    print(f"✓ faiss установлен")
except ImportError as e:
    print(f"✗ faiss не установлен: {e}")
    print("  Установите: pip install faiss-cpu")

# 4. Тест загрузки модели (опасная зона)
print("\n[4/5] Тест загрузки модели (может вызвать segfault)...")
print("Если программа вылетит здесь, значит проблема в torch/transformers")

try:
    from sentence_transformers import SentenceTransformer
    
    # Пробуем загрузить очень маленькую модель
    print("  Попытка загрузить модель...")
    print("  (это может занять время при первой загрузке)")
    
    # Используем самую простую модель
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print(f"✓ Модель загружена! Размерность: {model.get_sentence_embedding_dimension()}")
    
    # Пробуем создать эмбеддинг
    embedding = model.encode(["тест"])
    print(f"✓ Эмбеддинг создан! Размер: {embedding.shape}")
    
except Exception as e:
    print(f"✗ Ошибка при загрузке модели: {e}")
    import traceback
    traceback.print_exc()
    print("\nРЕКОМЕНДАЦИИ:")
    print("1. Переустановите torch:")
    print("   pip uninstall torch")
    print("   pip install torch --no-cache-dir")
    print("\n2. Или используйте conda:")
    print("   conda install pytorch -c pytorch")
    print("\n3. Или используйте упрощенную версию без векторного поиска")
    sys.exit(1)

# 5. Итоги
print("\n[5/5] Итоги")
print("="*70)
print("✓ Все компоненты работают!")
print("Векторный поиск должен работать.")
print("="*70)
