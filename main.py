import sys

from PyQt6.QtWidgets import QApplication

from app.config.config_loader import ConfigLoader
from app.logger.data_logger import DataLogger
from app.sensors.sensor_controller import SensorController
from app.ui.main_window import MainWindow


def main() -> int:
    config = ConfigLoader("config.yaml")

    app = QApplication(sys.argv)

    logger = DataLogger(config.logging_config)
    logger.log_system("start")

    window = MainWindow(config, logger)

    controller = SensorController(config)
    controller.state_updated.connect(window.update_sensors)
    controller.unload_detected.connect(window.on_unload)

    app.aboutToQuit.connect(controller.stop)
    app.aboutToQuit.connect(controller.wait)
    app.aboutToQuit.connect(lambda: logger.log_system("stop"))

    window.show()
    controller.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
