import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.metrics import accuracy_score

class JiminationModel:
    def __init__(self, input_shape=(28, 28, 1), num_classes=10):
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = self._build_model()
        self.history = []  # История изменений и их "корректности"

    # Дополним класс JiminationModel
    def meta_optimize(self, x_train, y_train, trials=10):
        """Ищет лучшие параметры через случайный поиск."""
        best_accuracy = 0
        best_params = {'lr': 0.001, 'neurons': 128}
        
        for _ in range(trials):
            lr = np.random.uniform(0.0001, 0.01)
            neurons = np.random.choice([64, 128, 256])
            self.model = self._build_model(lr=lr, neurons=neurons)
            accuracy = self.train(x_train, y_train)
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_params = {'lr': lr, 'neurons': neurons}
        
        self.model = self._build_model(**best_params)
        print(f"Meta-optimized: LR={best_params['lr']:.5f}, Neurons={best_params['neurons']}")
    
    def _build_model(self, lr=0.001, neurons=128):
        """Создаёт модель с заданными параметрами."""
        model = models.Sequential([
            layers.Flatten(input_shape=self.input_shape),
            layers.Dense(neurons, activation='relu'),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        return model
    
    def train(self, x_train, y_train, epochs=1):
        """Обучает модель и возвращает точность."""
        self.model.fit(x_train, y_train, epochs=epochs, verbose=0)
        _, accuracy = self.model.evaluate(x_train, y_train, verbose=0)
        return accuracy
    
    def jiminate(self, x_train, y_train, max_steps=5):
        """Рекурсивно применяет джиминацию."""
        for step in range(max_steps):
            # Текущая точность до изменений
            old_accuracy = self.train(x_train, y_train)
            
            # Меняем гиперпараметры (P -> ¬P)
            new_lr = np.random.uniform(0.0001, 0.01)  # Новый learning rate
            new_neurons = np.random.choice([64, 128, 256])  # Новый размер слоя
            
            # Пересобираем модель с новыми параметрами
            self.model = self._build_model(lr=new_lr, neurons=new_neurons)
            
            # Проверяем "корректность" (точность не упала более чем на 10%)
            new_accuracy = self.train(x_train, y_train)
            is_correct = new_accuracy >= old_accuracy * 0.9
            
            # Записываем изменение
            self.history.append({
                'step': step,
                'old_lr': self.model.optimizer.learning_rate.numpy(),
                'new_lr': new_lr,
                'old_neurons': self.model.layers[1].units,
                'new_neurons': new_neurons,
                'old_accuracy': old_accuracy,
                'new_accuracy': new_accuracy,
                'is_correct': is_correct
            })
            
            print(f"Step {step}: LR={new_lr:.5f}, Neurons={new_neurons}, "
                  f"Accuracy={new_accuracy:.3f}, Correct={is_correct}")
            
            # Если изменение некорректно, откатываем (опционально)
            if not is_correct:
                self.model = self._build_model(lr=old_lr, neurons=old_neurons)

# Загрузка данных
(x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
x_train = x_train / 255.0  # Нормализация

# Инициализация и запуск джиминации
model = JiminationModel()
model.jiminate(x_train, y_train, max_steps=5)

# Вывод истории изменений
for change in model.history:
    print(f"Step {change['step']}: "
          f"LR {change['old_lr']:.5f} -> {change['new_lr']:.5f}, "
          f"Neurons {change['old_neurons']} -> {change['new_neurons']}, "
          f"Accuracy {change['old_accuracy']:.3f} -> {change['new_accuracy']:.3f}, "
          f"Correct: {change['is_correct']}")