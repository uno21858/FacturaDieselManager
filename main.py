import sys
from PySide6 import QtWidgets as qtw
from logger_config import logger
from Principal.Principal_Window import MainWindow

def main():
    app = qtw.QApplication(sys.argv)

    logger.info("Iniciando la aplicacion principal.")
    ventana_principal = MainWindow()
    ventana_principal.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
