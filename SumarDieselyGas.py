import customtkinter as ctk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET
from datetime import datetime
import ctypes

def traducir_mes(fecha):
    meses = {
        "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
        "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
        "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
    }
    for ingles, espanol in meses.items():
        fecha = fecha.replace(ingles, espanol)
    return fecha

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
                messagebox.showwarning("Advertencia", f"La factura no pertenece a la gasolinera Colón.\nNombre del proveedor encontrado: \n{nombre}")
                return False
        else:
            messagebox.showerror("Error", "No se encontró el nodo Emisor en el archivo XML.")
            return False
    except Exception as e:
        messagebox.showerror("Error", f"Error al procesar el archivo: {e}")
        return False

def verificar_rfc(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}

        receptor = root.find('.//cfdi:Receptor', namespaces)
        if receptor is not None:
            rfc = receptor.attrib.get('Rfc', '').upper()
            if rfc == 'GCO740121MC5' or rfc == 'TSB740430489':
                return True
            else:
                messagebox.showwarning("Advertencia", f"La factura no pertenece a la gasolinera Colón.\nRFC encontrado: {rfc}")
                return False
        else:
            messagebox.showerror("Error", "No se encontró el nodo Receptor en el archivo XML.")
            return False
    except Exception as e:
        messagebox.showerror("Error", f"Error al procesar el archivo: {e}")
        return False

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
        messagebox.showerror("Error", f"Error al procesar el archivo: {e}")
        return "Desconocido", "Desconocido"

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
        messagebox.showerror("Error", f"Error al procesar el archivo: {e}")
        return 0, 0, 0

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("Archivos XML", "*.xml")])
    if file_path:
        if verificar_rfc(file_path) and verificar_proveedor(file_path):
            diesel_liters, diesel_price, gasoline_price = extract_fuel_data(file_path)
            diesel_liters_label.configure(text=f"Total de litros de diésel: {diesel_liters:,.3f}")
            diesel_price_label.configure(text=f"Total del precio del diésel: ${diesel_price:,.2f}")
            gasoline_price_label.configure(text=f"Total del precio de la gasolina: ${gasoline_price:,.2f}")
            fecha, folio = sacar_datos(file_path)
            fecha_label.configure(text=f"Fecha de la factura: {fecha}")
            folio_label.configure(text=f"Folio de la factura: {folio}")

# configureuración de la interfaz gráfica
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Sumador de Combustibles desde Facturas XML")

# Encabezado
header_frame = ctk.CTkFrame(root)
header_frame.pack(fill="x")

title_label = ctk.CTkLabel(header_frame, text="Sumador de Diesel y Gas", font=("Arial", 20, "bold"))
title_label.pack(padx=10, pady=10)

fecha_label = ctk.CTkLabel(header_frame, text="Fecha de la factura: ", font=("Arial", 18))
fecha_label.pack(padx=10, pady=5)

folio_label = ctk.CTkLabel(header_frame, text="Folio de la factura: ", font=("Arial", 18))
folio_label.pack(padx=10, pady=5)

# Contenido principal
content_frame = ctk.CTkFrame(root)
content_frame.pack(fill="both", expand=True)

diesel_liters_label = ctk.CTkLabel(content_frame, text="Total de litros de diésel: 0.00", font=("Arial", 16))
diesel_liters_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

diesel_price_label = ctk.CTkLabel(content_frame, text="Total del precio del diésel: $0.00", font=("Arial", 16))
diesel_price_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

gasoline_price_label = ctk.CTkLabel(content_frame, text="Total del precio de la gasolina: $0.00", font=("Arial", 16))
gasoline_price_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)

# Botones
button_frame = ctk.CTkFrame(root)
button_frame.pack(fill="x")

open_button = ctk.CTkButton(button_frame, text="Abrir Archivo XML", command=open_file, font=("Arial", 16))
open_button.grid(row=0, column=0, padx=20, pady=20)

exit_button = ctk.CTkButton(button_frame, text="Salir", command=root.quit, font=("Arial", 16))
exit_button.grid(row=0, column=1, padx=20, pady=20)

# Ajustar las columnas en los frames
button_frame.grid_columnconfigure(0, weight=1)
button_frame.grid_columnconfigure(1, weight=1)
content_frame.grid_columnconfigure(0, weight=1)

myappid = 'mycompany.myproduct.subproduct.version'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# Iniciar el bucle principal
root.iconbitmap('icon.ico')
root.mainloop()
