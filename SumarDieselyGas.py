import xml.etree.ElementTree as ET
from datetime import datetime

# Traduce los nombres de los meses del inglés al español
def traducir_mes(fecha):
    meses = {
        "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
        "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
        "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
    }
    for ingles, espanol in meses.items():
        fecha = fecha.replace(ingles, espanol)
    return fecha

# Verifica si el proveedor del XML corresponde a "Gasolinera Colón"
def verificar_proveedor(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}

        receptor = root.find('.//cfdi:Emisor', namespaces)
        if receptor is not None:
            nombre = receptor.attrib.get('Nombre', '').upper()
            if nombre == "GASOLINERA COLON":
                return True
            else:
                return f"La factura no pertenece a la gasolinera Colón. Nombre encontrado: {nombre}"
        else:
            return "No se encontró el nodo Emisor en el archivo XML."
    except Exception as e:
        return f"Error al procesar el archivo: {e}"

# Verifica si el RFC en el XML coincide con uno esperado
def verificar_rfc(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}

        receptor = root.find('.//cfdi:Receptor', namespaces)
        if receptor is not None:
            rfc = receptor.attrib.get('Rfc', '').upper()
            if rfc in ['GCO740121MC5', 'TSB740430489']:
                return True
            else:
                return f"El RFC no coincide. RFC encontrado: {rfc}"
        else:
            return "No se encontró el nodo Receptor en el archivo XML."
    except Exception as e:
        return f"Error al procesar el archivo: {e}"

# Extrae la fecha y el folio del XML
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
        return f"Error al procesar el archivo: {e}", "Desconocido"

# Extrae datos sobre litros y precios de diésel y gasolina del XML
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
        return f"Error al procesar el archivo: {e}", 0, 0, 0
