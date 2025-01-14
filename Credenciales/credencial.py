import time
import sys
from PySide6 import QtWidgets as qtw
from Credenciales.UI.credenciales_windows import Ui_Form
from utils import crear_archivos_credenciales
from logger_config import logger


class UiForm(qtw.QDialog, Ui_Form):  # Cambia de QWidget a QDialog
    def __init__(self, callback):
        super().__init__()
        self.setupUi(self)
        self.callback = callback
        self.pb_Cancel.clicked.connect(self.reject)
        self.pb_Ok.clicked.connect(self.guardar_credenciales)

    def guardar_credenciales(self):
        try:
            rfc = self.le_RFC.text().strip().upper()
            password = self.le_passwd.text().strip()

            if len(rfc) != 12:
                self.lb_message.setText("RFC inválido. Debe tener 12 caracteres.")
                logger.warning("Intento de guardar credenciales con RFC inválido.")
                return

            if not password:
                self.lb_message.setText("La contraseña no puede estar vacía.")
                logger.warning("Intento de guardar credenciales sin contraseña.")
                return

            crear_archivos_credenciales(rfc=rfc, password=password)
            self.lb_message.setText("Credenciales guardadas correctamente.")
            logger.info("Credenciales guardadas correctamente.")
            time.sleep(1)
            self.accept()
            if self.callback:
                self.callback()
        except Exception as e:
            logger.error(f"Error al guardar credenciales: {e}")
            self.lb_message.setText("Ocurrió un error al guardar las credenciales.")


    def closeEvent(self, event):
        logger.info("Ventana de credenciales cerrada.")
        super().closeEvent(event)


def log_uncaught_exceptions(exctype, value, tb):
    logger.critical("Excepción no manejada", exc_info=(exctype, value, tb))
    sys.__excepthook__(exctype, value, tb)

def MainCreateCredentials():
    sys.excepthook = log_uncaught_exceptions
    window = UiForm(callback=None)
    window.show()

