from PySide6.QtCore import QThread, Signal
from DescargaFacturasSAT.DescargaFactura import MainDescarga as _MainDescarga


class DownloadWorker(QThread):
    error = Signal(str, str)
    warning = Signal(str, str)
    info = Signal(str, str)
    credentials_needed = Signal()

    def __init__(self, mes, anio):
        super().__init__()
        self.mes = mes
        self.anio = anio

    def run(self):
        try:
            _MainDescarga(self.mes, self.anio, worker_thread=self)
        except Exception as e:
            self.error.emit("Error", f"Error inesperado: {str(e)}")