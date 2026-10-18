
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from database.repository import GameRepository
from services.data_service import DataService
from ui.main_window import MainWindow


def main():
    
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)
    app.setApplicationName("Video Game Database Explorer")
    app.setOrganizationName("CS200 Data Structures & Algorithms")

   
    repo = GameRepository()
    data_service = DataService(repo)

   
    window = MainWindow(data_service)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

