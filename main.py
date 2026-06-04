import os
import sys
from pathlib import Path

# Material style до создания QApplication
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

from app.bridge.app_bridge import AppBridge
from app.config.config_loader import ConfigLoader
from app.logger.data_logger import DataLogger
from app.sensors.sensor_controller import SensorController
from app.stats.statistics_collector import StatisticsCollector
from app.stats.statistics_storage import StatisticsStorage

QML_DIR = Path(__file__).parent / "qml"


def main() -> int:
    config = ConfigLoader("config.yaml")

    # QApplication нужен для диалогов; QGuiApplication достаточен для чистого QML
    app = QApplication(sys.argv)

    logger    = DataLogger(config.logging_config)
    logger.log_system("start")

    data_dir  = config.logging_config.get("data_dir", "data")
    storage   = StatisticsStorage(data_dir)
    collector = StatisticsCollector(config, storage)

    # ── Бридж Python ↔ QML ────────────────────────────────────────────────
    bridge = AppBridge(config, logger, collector)

    # ── Сенсор-контроллер ─────────────────────────────────────────────────
    controller = SensorController(config)
    controller.state_updated.connect(bridge.onSensorUpdate)
    controller.state_updated.connect(collector.on_sensor_update)
    controller.unload_detected.connect(bridge.onUnload)
    controller.unload_detected.connect(collector.on_unload)

    # ── QML движок ────────────────────────────────────────────────────────
    engine = QQmlApplicationEngine()

    # Путь до модуля pages/
    engine.addImportPath(str(QML_DIR))

    # Бридж доступен в QML как глобальное свойство bridge
    engine.rootContext().setContextProperty("bridge", bridge)

    engine.load(QUrl.fromLocalFile(str(QML_DIR / "main.qml")))

    if not engine.rootObjects():
        print("Не удалось загрузить QML", file=sys.stderr)
        return 1

    app.aboutToQuit.connect(controller.stop)
    app.aboutToQuit.connect(controller.wait)
    app.aboutToQuit.connect(collector.shutdown)
    app.aboutToQuit.connect(lambda: logger.log_system("stop"))

    controller.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
