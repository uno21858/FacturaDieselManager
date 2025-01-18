import sys
import time
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

from PySide6 import QtWidgets as qtw
from PySide6.QtWidgets import QFileSystemModel, QMessageBox
from PySide6.QtCore import QFileSystemWatcher, QModelIndex

from utils import base_archivos
from Principal.UI.principal_window import Ui_MainWindow
from DescargaFacturasSAT.DescargaFactura import MainDescarga
from logger_config import logger

class QTextEditHandler(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)

class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setup_logger()

        # Conectar señales
        self.ui.btn_download.clicked.connect(self.descargafacturas)
        self.ui.cB_months.currentTextChanged.connect(self.preguntar_mes)
        self.ui.Dte_year.dateChanged.connect(self.preguntar_anio)

        self.ui.treeView.setAlternatingRowColors(True)
        self.file_system_model = QFileSystemModel()
        base_xml = base_archivos + r"\xml_descargado"
        self.file_system_model.setRootPath(base_xml)
        self.ui.treeView.setHeaderHidden(True)
        self.file_system_model.index(base_xml)
        self.ui.treeView.setModel(self.file_system_model)
        self.ui.treeView.setRootIndex(self.file_system_model.index(base_xml))

        self.ui.treeView.setColumnHidden(1, True)
        self.ui.treeView.setColumnHidden(2, True)
        self.ui.treeView.setColumnHidden(3, True)
        self.ui.treeView.setHeaderHidden(True)
        self.ui.treeView.clicked.connect(self.on_treeview_click)
        self.inicializar_supervisor()


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
        logger.info(f"Descargando facturas para el mes {str(self.mes_numerico_seleccionado)} del año {str(self.anio_seleccionado)}")
        MainDescarga(self)

    def on_treeview_click(self, index: QModelIndex):
        file_path = self.file_system_model.filePath(index)

        if os.path.isfile(file_path) and file_path.endswith('.xml'):
            logger.info(f"Procesando archivo seleccionado:")

            fecha, folio = sacar_datos(file_path)
            diesel_liters, diesel_price, gasoline_price = extract_fuel_data(file_path)

            # Actualizar etiquetas
            self.ui.lb_fechaEmision.setText(fecha)
            self.ui.lb_LitersDiesel.setText(f"{diesel_liters:,.2f}")
            self.ui.lb_PriceDiesel.setText(f"${diesel_price:,.2f}")
            self.ui.lb_FolioFactura.setText(f"D{folio}")
            self.ui.lb_PriceGas.setText(f"${gasoline_price:,.2f}")
        else:
            QMessageBox.warning(self, "Archivo no válido", "Por favor selecciona un archivo XML válido.")
    # Actualizar constantemente el tree
    def inicializar_supervisor(self):
        self.watcher = QFileSystemWatcher()
        base_xml = base_archivos + r"\xml_descargado"
        if os.path.exists(base_xml):
            self.watcher.addPath(base_xml)
            self.watcher.directoryChanged.connect(self.actualizar_treeview)
            logger.info(f"Supervisando la carpeta: {base_xml}")
        else:
            logger.error(f"La carpeta '{base_xml}' no existe. No se pudo inicializar el supervisor.")

    def actualizar_treeview(self):
        base_xml = base_archivos + r"\xml_descargado"
        if os.path.exists(base_xml):
            self.file_system_model.setRootPath(base_xml)
            self.ui.treeView.setRootIndex(self.file_system_model.index(base_xml))
            logger.info("Árbol de facturas actualizado.")
        else:
            logger.warning("La carpeta de facturas no existe.")

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

        namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
        total_diesel_liters = 0
        total_diesel_price = 0
        total_gasoline_price = 0

        for concept in root.findall('.//cfdi:Concepto', namespaces):
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


def ventana_principal():
    sys.excepthook = log_uncaught_exceptions

    app = qtw.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


