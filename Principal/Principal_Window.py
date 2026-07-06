import sys
import time
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

from PySide6 import QtWidgets as qtw
from PySide6.QtWidgets import QFileSystemModel, QMessageBox
from PySide6.QtCore import QModelIndex, QObject, Signal

from utils import base_archivos, conceptos_cfdi
from Principal.UI.principal_window import Ui_MainWindow
from logger_config import logger

from worker_thread import DownloadWorker

class QTextEditHandler(logging.Handler, QObject):
    # Señal para cruzar del hilo de descarga al hilo de la UI (tocar widgets desde otro hilo truena)
    _nuevo_log = Signal(str)

    def __init__(self, text_edit):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.text_edit = text_edit
        # Tope de líneas: al llegar al límite, Qt descarta las más viejas solo
        text_edit.document().setMaximumBlockCount(500)
        self._nuevo_log.connect(self._agregar_linea)

    def emit(self, record):
        # La UI muestra solo la primera línea, corta; el detalle completo queda en application.log
        msg = record.getMessage().splitlines()[0]
        if len(msg) > 160:
            msg = msg[:160] + "…"
        self._nuevo_log.emit(msg)

    def _agregar_linea(self, msg):
        self.text_edit.append(msg)
        barra = self.text_edit.verticalScrollBar()
        barra.setValue(barra.maximum())

APP_VERSION = "1.2.0"

class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Factura Diesel Manager v{APP_VERSION}")

        self.download_worker = None

        self.setup_logger()

        # Conectar señales
        self.ui.btn_download.clicked.connect(self.descargafacturas)
        self.ui.cB_months.currentTextChanged.connect(self.preguntar_mes)
        self.ui.Dte_year.dateChanged.connect(self.preguntar_anio)

        # QFileSystemModel se auto-actualiza cuando cambia el contenido de las carpetas
        self.ui.treeView.setAlternatingRowColors(True)
        self.file_system_model = QFileSystemModel()
        base_xml = os.path.join(base_archivos, "xml_descargado")
        self.file_system_model.setRootPath(base_xml)
        self.ui.treeView.setModel(self.file_system_model)
        self.ui.treeView.setRootIndex(self.file_system_model.index(base_xml))
        for col in (1, 2, 3):
            self.ui.treeView.setColumnHidden(col, True)
        self.ui.treeView.setHeaderHidden(True)
        self.ui.treeView.clicked.connect(self.on_treeview_click)


    def setup_logger(self):
        handler = QTextEditHandler(self.ui.DispLogs)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def preguntar_mes(self):
        meses_a_descargar = {
            "Enero": "1", "Febrero": "2", "Marzo": "3", "Abril": "4",
            "Mayo": "5", "Junio": "6", "Julio": "7", "Agosto": "8",
            "Septiembre": "9", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
        }

        mes_actual = int(time.strftime("%m"))
        anio_actual = int(time.strftime("%Y"))
        mes_seleccionado_texto = self.ui.cB_months.currentText()
        self.mes_numerico_seleccionado = int(meses_a_descargar.get(mes_seleccionado_texto, 0))
        self.anio_seleccionado = self.ui.Dte_year.date().year()

        if self.anio_seleccionado > anio_actual or (self.anio_seleccionado == anio_actual and self.mes_numerico_seleccionado > mes_actual):
            logger.error("Mes seleccionado inválido: no puede ser en el futuro.")
            qtw.QMessageBox.warning(self, "Mes inválido", "El mes seleccionado no puede ser mayor al mes actual.")
            self.mes_numerico_seleccionado = None
        else:
            logger.info(f"Mes seleccionado válido: {mes_seleccionado_texto} ({self.mes_numerico_seleccionado})")

    def preguntar_anio(self):
        self.anio_seleccionado = self.ui.Dte_year.date().year()
        anio_actual = int(time.strftime("%Y"))
        if self.anio_seleccionado > anio_actual:
            logger.error("Año seleccionado inválido.")
            qtw.QMessageBox.warning(self, "Año inválido", "El año seleccionado no puede ser mayor al año actual.")
            self.anio_seleccionado = None
        else:
            logger.info(f"Año seleccionado: {self.anio_seleccionado}")

    def descargafacturas(self):
        if self.download_worker is not None and self.download_worker.isRunning():
            logger.warning("Ya hay una descarga en progreso")
            return

        # Leer la selección actual del combo aquí, sin depender de que las señales hayan corrido
        self.preguntar_mes()
        if self.mes_numerico_seleccionado is None or self.anio_seleccionado is None:
            logger.error("Mes o año seleccionado inválido")
            return

        logger.info(
            f"Descargando facturas para el mes {str(self.mes_numerico_seleccionado)} del año {str(self.anio_seleccionado)}")

        self.ui.btn_download.setEnabled(False)

        # Pasar solo los datos, NO la ventana completa
        self.download_worker = DownloadWorker(
            self.mes_numerico_seleccionado,
            self.anio_seleccionado
        )
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.warning.connect(self.on_download_warning)
        self.download_worker.info.connect(self.on_download_info)
        self.download_worker.credentials_needed.connect(self.on_credentials_needed)
        self.download_worker.start()

    def on_treeview_click(self, index: QModelIndex):
        file_path = self.file_system_model.filePath(index)

        if not os.path.isfile(file_path):
            return  # carpetas: solo navegación, sin popup
        if not file_path.endswith('.xml'):
            QMessageBox.warning(self, "Archivo no válido", "Por favor selecciona un archivo XML válido.")
            return

        fecha, folio = sacar_datos(file_path)
        diesel_liters, diesel_price, gasoline_price = extract_fuel_data(file_path)

        # Actualizar etiquetas
        self.ui.lb_fechaEmision.setText(fecha)
        self.ui.lb_LitersDiesel.setText(f"{diesel_liters:,.2f}")
        self.ui.lb_PriceDiesel.setText(f"${diesel_price:,.2f}")
        self.ui.lb_FolioFactura.setText(f"D{folio}")
        self.ui.lb_PriceGas.setText(f"${gasoline_price:,.2f}")

    def on_download_finished(self):
        self.ui.btn_download.setEnabled(True)
        logger.info("Descarga completada")


    def on_download_error(self, title, message):
        self.ui.btn_download.setEnabled(True)
        logger.error(f"Error en descarga: {message}")
        qtw.QMessageBox.critical(self, title, message)

    def on_download_warning(self, title, message):
        qtw.QMessageBox.warning(self, title, message)

    def on_download_info(self, title, message):
        qtw.QMessageBox.information(self, title, message)

    def on_credentials_needed(self):
        self.ui.btn_download.setEnabled(True)
        qtw.QMessageBox.warning(
            self,
            "Credenciales faltantes",
            "No se encontraron las credenciales. Por favor, introdúzcalas para continuar.",
            qtw.QMessageBox.Ok
        )
        from Credenciales.credencial import UiForm as CredencialesForm
        ventana_credenciales = CredencialesForm(callback=lambda: None)
        ventana_credenciales.exec()

# Funciones externas para suma de diesel y gasolina
def traducir_mes(fecha):
    meses = {
        "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
        "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
        "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
    }
    for ingles, espanol in meses.items():
        fecha = fecha.replace(ingles, espanol)
    return fecha

def sacar_datos(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
        comprobante = root if root.tag.endswith('Comprobante') else root.find('.//cfdi:Comprobante', namespaces)

        if comprobante is not None:
            fecha_original = comprobante.attrib.get('Fecha', 'Fecha no encontrada')
            folio = comprobante.attrib.get('Folio', 'Folio no encontrado')
            fecha_formateada = (
                datetime.strptime(fecha_original[:10], "%Y-%m-%d").strftime("%d de %B %Y")
                if fecha_original != 'Fecha no encontrada' else "Fecha no encontrada"
            )
        else:
            fecha_formateada = "Fecha no encontrada"
            folio = "Folio no encontrado"

        fecha_formateada = traducir_mes(fecha_formateada)
        return fecha_formateada, folio
    except Exception as e:
        logger.error(f"Error al procesar el archivo: {e}")
        return "Error", "Error"

def extract_fuel_data(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        total_diesel_liters = 0
        total_diesel_price = 0
        total_gasoline_price = 0

        for concept in conceptos_cfdi(root):
            description = concept.attrib.get('Descripcion', '').lower()
            liters = float(concept.attrib.get('Cantidad', 0))
            price = float(concept.attrib.get('Importe', 0))

            if 'diesel' in description:
                total_diesel_liters += liters
                total_diesel_price += price
            elif 'magna' in description or 'premium' in description:
                total_gasoline_price += price

        return total_diesel_liters, total_diesel_price, total_gasoline_price
    except Exception as e:
        logger.error(f"Error al procesar el archivo: {e}")
        return 0, 0, 0

def log_uncaught_exceptions(exctype, value, tb):
    logger.critical("Excepción no manejada", exc_info=(exctype, value, tb))
    sys.__excepthook__(exctype, value, tb)


