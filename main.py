import sys

from PyQt6.QtWidgets import QApplication

from app.config.config_loader import ConfigLoader
from app.logger.data_logger import DataLogger
from app.sensors.sensor_controller import SensorController
from app.stats.statistics_collector import StatisticsCollector
from app.stats.statistics_storage import StatisticsStorage
from app.ui.main_window import MainWindow


def main() -> int:
    config = ConfigLoader("config.yaml")

    app = QApplication(sys.argv)

    logger = DataLogger(config.logging_config)
    logger.log_system("start")

    data_dir = config.logging_config.get("data_dir", "data")
    storage = StatisticsStorage(data_dir)
    collector = StatisticsCollector(config, storage)

    window = MainWindow(config, logger, collector)

    controller = SensorController(config)
    controller.state_updated.connect(window.update_sensors)
    controller.state_updated.connect(collector.on_sensor_update)
    controller.unload_detected.connect(window.on_unload)
    controller.unload_detected.connect(collector.on_unload)

    app.aboutToQuit.connect(controller.stop)
    app.aboutToQuit.connect(controller.wait)
    app.aboutToQuit.connect(collector.shutdown)
    app.aboutToQuit.connect(lambda: logger.log_system("stop"))

    window.show()
    controller.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
