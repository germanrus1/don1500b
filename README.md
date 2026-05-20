# Бортовой компьютер Дон 1500б на Raspberry Pi 5

Система мониторинга датчиков комбайна в реальном времени с интерфейсом на 7" сенсорном дисплее (1200×600).

**Технологический стек:** PyQt6 + Python 3.11+ + RPi.GPIO

## 🎯 Основные возможности

- **Мониторинг датчиков в реальном времени**: обороты барабана, колосовой, соломотряса, вентилятора
- **Отслеживание разгрузок бункера**: подсчет количества и культуры
- **Логирование данных**: CSV файлы по датам с полной историей событий
- **Система ошибок**: история ошибок датчиков с временем и статусом
- **Адаптивный интерфейс**: шрифты и цвета настраиваются через конфиг
- **Ночной режим**: темная тема для комфортной работы в темноте
- **Отладочный режим**: отдельное приложение для имитации сигналов датчиков

## 📋 Требования

### Оборудование
- Raspberry Pi 5 (или Pi 4, 3B+)
- Сенсорный дисплей 1200×600 (7 дюймов) с HDMI и USB Type-C
- Модуль оптической изоляции 8-канальный (PLC 24V to 5V)
- Датчики: импульсные, дискретные, аналоговые
- Кабели GPIO, питание 24V/5V, разъемы

### ОС и Софт
- **OS**: Ubuntu 24.04 LTS (на Raspberry Pi)
- **Python**: 3.11+
- **Зависимости**: PyQt6, PyYAML, RPi.GPIO, gpiozero

## 🚀 Установка

### 1. Клонирование / подготовка проекта

```bash
mkdir -p ~/don1500b
cd ~/don1500b
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Создание структуры папок

```bash
mkdir -p app/{ui,sensors,config,logger,dev}
mkdir -p data
touch config.yaml
```

### 4. Копирование конфига

Скопируйте `config.yaml` в корень проекта и отредактируйте GPIO пины под вашу схему подключения.

## 📂 Структура проекта

```
don_1500b/
├── config.yaml                  # Конфигурация датчиков и интерфейса
├── main.py                      # Точка входа
├── requirements.txt             # Зависимости
├── README.md                    # Этот файл
│
├── app/
│   ├── __init__.py
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py       # Главное окно (PyQt6)
│   │   ├── menu_dialog.py       # Меню и диалоги
│   │   └── styles.py            # Стили и шрифты
│   │
│   ├── sensors/
│   │   ├── __init__.py
│   │   ├── sensor_controller.py # Контроллер датчиков (фоновый поток)
│   │   ├── sensor_base.py       # Базовый класс датчика
│   │   ├── error_handler.py     # Обработка ошибок
│   │   └── unload_logic.py      # Логика разгрузки (отдельный модуль)
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── config_loader.py     # Загрузчик YAML
│   │
│   ├── logger/
│   │   ├── __init__.py
│   │   └── data_logger.py       # Логирование в CSV
│   │
│   └── dev/
│       ├── __init__.py
│       ├── debug_window.py      # Отладочное окно (dev_mode)
│       └── mock_sensors.py      # Мок-датчики
│
├── data/
│   └── YYYY-MM-DD.csv          # Логи по датам (создаются автоматически)
│
└── tests/
    └── test_*.py               # Unit тесты (опционально)
```

## ⚙️ Конфигурация (config.yaml)

### Основные параметры

**Режим работы:**
```yaml
mode: prod    # prod (боевой) или dev (с отладочным окном)
```

**Датчики:**
```yaml
sensors:
  polling_frequency_hz: 50  # Опрос каждые 20 мс
  list:
    drum:
      gpio: 17
      type: impulse
      nominal_rpm: 800
      warn_low: 600
      warn_high: 1000
      error_threshold_low: 100
      error_duration_ms: 2000
      debounce_ms: 50
```

**Разгрузка бункера:**
```yaml
unload_logic:
  bin_full_sensor: 22
  min_full_duration_ms: 1000
  min_empty_duration_ms: 500
  debounce_ms: 100
```

**Интерфейс:**
```yaml
ui:
  resolution:
    width: 1200
    height: 600
  fonts:
    value: 28       # Основные значения
    label: 16       # Подписи
    time: 24        # Время
  theme: light      # light или dark
```

Полный пример см. в `config.yaml`.

## 🚀 Запуск приложения

### Боевой режим (prod)

```bash
python main.py
```

### Режим разработки (dev)

```bash
# В config.yaml установите mode: dev
mode: dev
python main.py
```

В отладочном окне:
- **Ползунки** для импульсных датчиков (0-2000 об/мин)
- **Чекбоксы** для дискретных датчиков (заполнен/пуст)
- Наблюдайте изменения в основном окне в реальном времени

### Пример инициализации приложения (PyQt6)

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QThread
from app.ui.main_window import MainWindow
from app.sensors.sensor_controller import SensorController

if __name__ == '__main__':
    app = QApplication([])
    
    # Запустить контроллер датчиков в отдельном потоке
    sensor_thread = QThread()
    sensor_controller = SensorController(config)
    sensor_controller.moveToThread(sensor_thread)
    sensor_thread.started.connect(sensor_controller.run)
    sensor_thread.start()
    
    # Главное окно
    main_window = MainWindow(sensor_controller)
    main_window.show()
    
    app.exec()
```

## 🔧 Архитектура

### Двухпоточная модель

**Фоновый поток (SensorController):**
- Опрашивает GPIO с частотой 50 Hz
- Применяет дебаунсинг и фильтрацию
- Рассчитывает об/мин
- Запускает ErrorHandler и UnloadLogic
- Отправляет данные в очередь Queue

**Основной поток (GUI):**
- PyQt5 интерфейс на 1200×600
- Берет данные из очереди Queue
- Обновляет экран в реальном времени
- Логирует события в CSV
- Обрабатывает нажатия на меню

### Взаимодействие компонентов

```
GPIO Датчики
      ↓
[Оптическая изоляция]
      ↓
RPi GPIO Пины
      ↓
SensorController (фоновый поток, 50 Hz)
      ├→ Дебаунсинг
      ├→ ErrorHandler (проверка ошибок)
      ├→ UnloadLogic (отслеживание разгрузок)
      ↓
Queue (потокобезопасная)
      ↓
MainWindow (основной поток, GUI)
      ├→ Отображение на экране
      ├→ Логирование в CSV
      └→ Обработка меню
```

## 📊 Логирование данных

### CSV формат

Файлы создаются автоматически: `data/2024-05-20.csv`

```
timestamp,event_type,sensor_name,value,unit,status,details
2024-05-20 10:30:45,reading,drum_rpm,850,rpm,ok,
2024-05-20 10:31:12,error,drum_rpm,150,rpm,warn_low,Below nominal 800
2024-05-20 10:32:00,unload,bin_level,0,bool,success,Grain unload counted
```

### Типы событий
- `reading` - обычное показание датчика
- `unload` - разгрузка бункера
- `error` - ошибка датчика (warn_low, warn_high, critical)
- `system` - системные события (старт, выключение)

## 🎨 Интерфейс

### Главный экран

```
┌─────────────────────────────────────────────────────┐
│ [МЕНЮ]              10:32:45                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│                    [⚠]  [⚠]              Барабан    │
│                                          850 об/мин │
│                                                      │
│                                          Колоса     │
│                                          420 об/мин │
│                                                      │
│                                          Вентилятор │
│                                          1200 об/мин│
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Визуальные элементы:**
- **[МЕНЮ]** - левый верхний угол, нажимаемая кнопка
- **Время** - верхний центр, обновляется каждую секунду
- **Иконки ошибок** - в центре экрана (красная для CRITICAL, оранжевая для WARN)
- **Показания датчиков** - правая часть экрана с адаптивными шрифтами из конфига

### Меню приложения

1. **Настройки**
   - День/Ночь режим
   - Яркость дисплея
   - Обновить конфиги

2. **Статистика за день**
   - Количество разгрузок
   - Время работы
   - Последние ошибки

3. **История ошибок**
   - Список последних 20 ошибок
   - Время, датчик, статус

4. **Выключение**
   - Подтверждение: "Уверены? (Да/Нет)"

## 🧪 Отладочное окно (dev_mode)

При `mode: dev`:

- **Слайдеры** для каждого импульсного датчика
- **Чекбоксы** для дискретных датчиков
- **Кнопки** для записи/воспроизведения сценариев
- Окна основного приложения и отладки рядом для наблюдения

## 📝 Логирование событий

### ErrorHandler

Датчик переходит в режим ошибки если:
1. Значение < `error_threshold_low` → красная иконка (CRITICAL)
2. Значение < `warn_low` или > `warn_high` → оранжевая иконка (WARN)
3. Ошибка отображается только после `error_duration_ms`

**Особенность:** Если барабан не вращается, ошибки других датчиков игнорируются.

### UnloadLogic

Разгрузка считается если:
1. Бункер был заполнен ≥ `min_full_duration_ms`
2. Затем стал пустым ≥ `min_empty_duration_ms`

Логируется: время, культура, количество разгрузок.

## 🐛 Отладка

### Добавить вывод в консоль

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Проверить GPIO пины

```python
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)  # Проверить пин 17
print(GPIO.input(17))
GPIO.cleanup()
```

### Проверить конфиг

```python
from app.config.config_loader import ConfigLoader
config = ConfigLoader('config.yaml')
print(config.get('sensors'))
```

## 🚢 Развертывание

### 1. На Raspberry Pi

```bash
# Обновить ОС
sudo apt update && sudo apt upgrade -y

# Установить Python и pip
sudo apt install python3 python3-pip python3-dev -y

# Клонировать проект
git clone <repo> ~/don1500b
cd ~/don1500b

# Установить зависимости
pip install -r requirements.txt

# Запустить
python main.py
```

### 2. Автозапуск при загрузке

Создать systemd сервис `/etc/systemd/system/don1500b.service`:

```ini
[Unit]
Description=Don 1500b Bortovoi Computer
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/don1500b
ExecStart=/usr/bin/python3 /home/pi/don1500b/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Активировать:
```bash
sudo systemctl enable don1500b
sudo systemctl start don1500b
```

## 📚 Документация

- `Архитектура_Дон_1500б.docx` - полное описание архитектуры
- `config.yaml` - пример конфигурации с комментариями
- Исходный код содержит docstring для каждого класса и метода

## 🤝 Участие в разработке

1. Создайте ветку: `git checkout -b feature/your-feature`
2. Сделайте коммит: `git commit -m "Add feature"`
3. Пушьте: `git push origin feature/your-feature`
4. Создайте Pull Request

## 📄 Лицензия

MIT License (если применимо)

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте GPIO подключение
2. Убедитесь, что config.yaml настроен правильно
3. Включите dev_mode и протестируйте отладочным окном
4. Посмотрите логи в `data/YYYY-MM-DD.csv`
5. Проверьте консоль: `python main.py 2>&1 | tee app.log`

---

**Версия**: 1.0.0  
**Последнее обновление**: 2024-05-20  
**Платформа**: Raspberry Pi 5 + Ubuntu 24.04 LTS  
**UI Framework**: PyQt6 6.7.0  
**Python**: 3.11+
