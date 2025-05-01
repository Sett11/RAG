import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
from sklearn.metrics import accuracy_score
from mylogger import Logger
from collections import deque
import random
import json

class JiminationModel:
    def __init__(self, input_shape=(28, 28, 1), num_classes=10):
        """Полная инициализация модели с поддержкой NAS и мета-обучения.
        
        Args:
            input_shape (tuple): Размерность входа (по умолчанию MNIST).
            num_classes (int): Количество классов классификации.
        """
        self.logger = Logger("JiminationModel", "jim.log")
        self.input_shape = input_shape
        self.num_classes = num_classes
        
        # Инициализация базовой модели
        self.model = self._build_basic_model()
        
        # История для мета-обучения (сохраняет последние N изменений)
        self.jimination_history = deque(maxlen=100)
        
        # Мета-модель для предсказания успешных изменений
        self.meta_model = self._build_meta_model()
        
        # NAS-пространство поиска
        self.nas_search_space = {
            'architecture': ['dense', 'conv', 'mixed'],
            'activations': ['relu', 'leaky_relu', 'swish'],
            'regularizers': [None, 'l1', 'l2', 'dropout'],
            'neurons': [64, 128, 256, 512],
            'learning_rates': [0.0001, 0.0005, 0.001, 0.005, 0.01]
        }
        
        self.logger.info("Model initialized with NAS and Meta-Learning support")

    def _build_basic_model(self, **params):
        """Строит модель с заданными параметрами (поддержка NAS)."""
        default_params = {
            'architecture': 'dense',
            'neurons': 128,
            'activation': 'relu',
            'regularizer': None,
            'lr': 0.001
        }
        params = {**default_params, **params}
        
        model = models.Sequential()
        model.add(layers.InputLayer(input_shape=self.input_shape))
        
        # Выбор архитектуры (раздел 5.2 статьи)
        if params['architecture'] == 'dense':
            model.add(layers.Flatten())
            self._add_dense_layer(model, params)
        elif params['architecture'] == 'conv':
            model.add(layers.Reshape((*self.input_shape, 1)))
            model.add(layers.Conv2D(32, (3, 3), activation=params['activation']))
            model.add(layers.MaxPooling2D((2, 2)))
            model.add(layers.Flatten())
            self._add_dense_layer(model, params)
        elif params['architecture'] == 'mixed':
            model.add(layers.Conv2D(16, (3, 3), activation=params['activation']))
            model.add(layers.MaxPooling2D((2, 2)))
            model.add(layers.Flatten())
            self._add_dense_layer(model, params)
        
        model.add(layers.Dense(self.num_classes, activation='softmax'))
        
        # Регуляризация (раздел 4.2.3 статьи)
        if params['regularizer'] == 'l1':
            for layer in model.layers:
                if hasattr(layer, 'kernel_regularizer'):
                    layer.kernel_regularizer = regularizers.l1(0.01)
        elif params['regularizer'] == 'l2':
            for layer in model.layers:
                if hasattr(layer, 'kernel_regularizer'):
                    layer.kernel_regularizer = regularizers.l2(0.01)
        elif params['regularizer'] == 'dropout':
            model.add(layers.Dropout(0.5))
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=params['lr']),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.logger.debug(f"Model built with params: {json.dumps(params, indent=2)}")
        return model

    def _add_dense_layer(self, model, params):
        """Добавляет dense-слой с учётом параметров NAS."""
        dense_layer = layers.Dense(
            params['neurons'],
            activation=params['activation']
        )
        model.add(dense_layer)

    def _build_meta_model(self):
        """Строит мета-модель для предсказания успешных изменений."""
        meta_model = models.Sequential([
            layers.Dense(64, activation='relu', input_shape=(7,)),
            layers.Dense(32, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        meta_model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        return meta_model

    def _generate_nas_parameters(self, exploration_rate=0.3):
        """Генерирует новые параметры с учётом истории (раздел 5.3 статьи).
        
        Args:
            exploration_rate (float): Вероятность случайного исследования.
        
        Returns:
            dict: Параметры для следующей архитектуры.
        """
        # Случайное исследование (exploration)
        if random.random() < exploration_rate or not self.jimination_history:
            params = {
                'architecture': random.choice(self.nas_search_space['architecture']),
                'neurons': random.choice(self.nas_search_space['neurons']),
                'activation': random.choice(self.nas_search_space['activations']),
                'regularizer': random.choice(self.nas_search_space['regularizers']),
                'lr': random.choice(self.nas_search_space['learning_rates'])
            }
            self.logger.debug("NAS: Random exploration")
            return params
        
        # Использование мета-модели (exploitation)
        successful_changes = [h['new_params'] for h in self.jimination_history if h['is_correct']]
        if successful_changes:
            # Выбираем параметры, похожие на успешные
            base_params = random.choice(successful_changes)
            
            # Модифицируем с небольшими изменениями
            params = {
                'architecture': base_params['architecture'],
                'neurons': base_params['neurons'] + random.choice([-64, 0, 64]),
                'activation': base_params['activation'],
                'regularizer': base_params['regularizer'],
                'lr': base_params['lr'] * random.choice([0.5, 1, 2])
            }
            # Ограничиваем значения
            params['neurons'] = max(64, min(512, params['neurons']))
            params['lr'] = max(0.0001, min(0.01, params['lr']))
            
            self.logger.debug("NAS: Exploitation with meta-guidance")
            return params
        
        return self._generate_nas_parameters(exploration_rate=1.0)  # Fallback

    def _prepare_meta_features(self, old_params, new_params, old_acc, new_acc):
        """Подготавливает признаки для мета-модели."""
        return np.array([
            old_params['lr'],
            old_params['neurons'],
            new_params['lr'] - old_params['lr'],
            new_params['neurons'] - old_params['neurons'],
            1 if new_params['architecture'] != old_params['architecture'] else 0,
            old_acc,
            new_acc - old_acc
        ])

    def _update_meta_model(self):
        """Обновляет мета-модель на основе истории."""
        if len(self.jimination_history) < 10:
            return
        
        X, y = [], []
        for record in self.jimination_history:
            features = self._prepare_meta_features(
                record['old_params'],
                record['new_params'],
                record['old_accuracy'],
                record['new_accuracy']
            )
            X.append(features)
            y.append(1 if record['is_correct'] else 0)
        
        X, y = np.array(X), np.array(y)
        self.meta_model.fit(X, y, epochs=5, verbose=0)
        self.logger.info("Meta-model updated with recent history")

    def _evaluate_jimination(self, old_acc, new_acc, old_params, new_params):
        """Расширенная оценка корректности с мета-моделью."""
        # Базовые критерии (раздел 4.2.1)
        accuracy_ok = new_acc >= old_acc * 0.9
        complexity_ok = 0.5 <= (new_params['neurons'] / old_params['neurons']) <= 2.0
        
        # Предсказание мета-модели
        meta_features = self._prepare_meta_features(
            old_params, new_params, old_acc, new_acc
        )
        meta_prediction = self.meta_model.predict(meta_features.reshape(1, -1))[0][0] > 0.5
        
        # Комплексное решение
        is_correct = accuracy_ok and complexity_ok and meta_prediction
        
        self.logger.debug(
            f"Jimination evaluation: "
            f"Accuracy OK={accuracy_ok}, "
            f"Complexity OK={complexity_ok}, "
            f"Meta prediction={meta_prediction}"
        )
        
        return is_correct

    def jiminate(self, x_train, y_train, x_val=None, y_val=None, max_steps=10):
        """Полный процесс джиминации с NAS и мета-обучением."""
        if x_val is None:
            x_val, y_val = x_train, y_train
            
        self.logger.info(f"Starting advanced jimination (max_steps={max_steps})")
        
        for step in range(max_steps):
            # 1. Фиксация текущего состояния
            old_params = self._get_current_params()
            old_acc = self.model.evaluate(x_val, y_val, verbose=0)[1]
            
            # 2. Генерация новых параметров через NAS
            new_params = self._generate_nas_parameters()
            
            # 3. Применение JIM-оператора
            self.model = self._build_basic_model(**new_params)
            self.model.fit(
                x_train, y_train,
                epochs=2,  # Увеличенное обучение для стабильности
                batch_size=128,
                verbose=0
            )
            new_acc = self.model.evaluate(x_val, y_val, verbose=0)[1]
            
            # 4. Расширенная проверка корректности
            is_correct = self._evaluate_jimination(old_acc, new_acc, old_params, new_params)
            
            # 5. Запись в историю
            self.jimination_history.append({
                'step': step,
                'old_params': old_params,
                'new_params': new_params,
                'old_accuracy': old_acc,
                'new_accuracy': new_acc,
                'is_correct': is_correct
            })
            
            # 6. Обратная связь и мета-обучение
            if is_correct:
                self.logger.info(
                    f"Step {step}: Successful jimination | "
                    f"Arch: {old_params['architecture']}→{new_params['architecture']} | "
                    f"Acc: {old_acc:.3f}→{new_acc:.3f}"
                )
            else:
                self.logger.warning(
                    f"Step {step}: Reverted jimination | "
                    f"Reason: {'Accuracy' if not (new_acc >= old_acc * 0.9) else 'Meta prediction'}"
                )
                self.model = self._build_basic_model(**old_params)  # Откат
            
            # 7. Периодическое обновление мета-модели
            if step % 3 == 0:
                self._update_meta_model()

    def _get_current_params(self):
        """Извлекает параметры текущей модели."""
        params = {
            'architecture': 'dense',
            'neurons': 128,
            'activation': 'relu',
            'regularizer': None,
            'lr': 0.001
        }
        
        # Анализ архитектуры
        if any('conv2d' in layer.name for layer in self.model.layers):
            params['architecture'] = 'conv' if len(self.model.layers) < 6 else 'mixed'
        
        # Поиск dense-слоя
        for layer in self.model.layers:
            if isinstance(layer, layers.Dense) and layer != self.model.layers[-1]:
                params['neurons'] = layer.units
                params['activation'] = layer.activation.__name__
                if hasattr(layer, 'kernel_regularizer') and layer.kernel_regularizer:
                    if 'l1' in str(layer.kernel_regularizer):
                        params['regularizer'] = 'l1'
                    else:
                        params['regularizer'] = 'l2'
        
        # Learning rate
        params['lr'] = float(self.model.optimizer.learning_rate.numpy())
        
        return params

    def get_architecture_description(self):
        """Возвращает текстовое описание архитектуры (для отчёта)."""
        desc = ["Model architecture:"]
        for i, layer in enumerate(self.model.layers):
            desc.append(f"{i+1}. {layer.__class__.__name__}")
            if isinstance(layer, layers.Dense):
                desc[-1] += f" (units={layer.units}, activation={layer.activation.__name__})"
            elif isinstance(layer, layers.Conv2D):
                desc[-1] += f" (filters={layer.filters}, kernel={layer.kernel_size})"
        return "\n".join(desc)

    def save_jimination_report(self, filename="jimination_report.txt"):
        """Генерирует полный отчёт в духе статьи."""
        report = [
            "Technotropic AI Development Report",
            "=" * 50,
            "Jimination Process Analysis",
            f"Total steps: {len(self.jimination_history)}",
            f"Successful transformations: {sum(h['is_correct'] for h in self.jimination_history)}",
            "\nCurrent Architecture:",
            self.get_architecture_description(),
            "\nParameter Evolution:"
        ]
        
        for step in self.jimination_history:
            report.append(
                f"\nStep {step['step']}:\n"
                f"Arch: {step['old_params']['architecture']} → {step['new_params']['architecture']}\n"
                f"Neurons: {step['old_params']['neurons']} → {step['new_params']['neurons']}\n"
                f"LR: {step['old_params']['lr']:.5f} → {step['new_params']['lr']:.5f}\n"
                f"Accuracy: {step['old_accuracy']:.3f} → {step['new_accuracy']:.3f}\n"
                f"Status: {'✓' if step['is_correct'] else '✗'}"
            )
        
        with open(filename, 'w') as f:
            f.write("\n".join(report))
        self.logger.info(f"Report saved to {filename}")

# Полный пример использования
if __name__ == "__main__":
    # Инициализация
    logger = Logger("Main", "jim.log")
    logger.info("Loading MNIST data...")
    (x_train, y_train), (x_val, y_val) = tf.keras.datasets.mnist.load_data()
    x_train, x_val = x_train / 255.0, x_val / 255.0
    
    # Создание и обучение модели
    logger.info("Initializing JiminationModel...")
    model = JiminationModel()
    
    # Первоначальная оценка
    initial_acc = model.model.evaluate(x_val, y_val, verbose=0)[1]
    logger.info(f"Initial accuracy: {initial_acc:.3f}")
    
    # Запуск джиминации
    logger.info("Starting advanced jimination process...")
    model.jiminate(x_train, y_train, x_val, y_val, max_steps=15)
    
    # Финальная оценка
    final_acc = model.model.evaluate(x_val, y_val, verbose=0)[1]
    logger.info(f"Final accuracy: {final_acc:.3f} (Improvement: {final_acc-initial_acc:.3f})")
    
    # Сохранение отчёта
    model.save_jimination_report()
    logger.info("Experiment completed successfully")