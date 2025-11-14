# --- pdf_generator.py ---
from fpdf import FPDF
import os
import sys

# --- Constantes (Datos de tu empresa) ---
EMPRESA_NOMBRE = "Development of Automation Systems and Industrial Control SA de CV"
EMPRESA_DIRECCION = "Ave Iztaccíhuatl MZ 40 Lt 1, Col. Adolfo Ruiz Cortines, Del. Coyoacán, CP. 04630"
VENDEDOR_NOMBRE = "Juan Manuel Tapia"
VENDEDOR_EMAIL = "juan_ma_t@outlook.com"

# Plantilla de Términos Comerciales
try:
    with open('terminos.txt', 'r', encoding='utf-8') as f:
        TERMINOS_COMERCIALES = f.read()
except FileNotFoundError:
    TERMINOS_COMERCIALES = """
    CONDICIONES COMERCIALES NO ENCONTRADAS. 
    Crear un archivo 'terminos.txt' en la misma carpeta.
    """

class PDF(FPDF):
    """Clase heredada para tener encabezado y pie de página personalizados"""
    def header(self):
        # self.image('logo.png', 10, 8, 33) # Descomentar si tienes un logo.png
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, EMPRESA_NOMBRE, 0, 1, 'C')
        self.set_font('Arial', '', 8)
        self.cell(0, 5, EMPRESA_DIRECCION, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-35) # Posición 3.5 cm desde abajo
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'ATENTAMENTE', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, VENDEDOR_NOMBRE, 0, 1, 'L')
        self.cell(0, 5, VENDEDOR_EMAIL, 0, 1, 'L')
        # Número de página
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def crear_pdf_cotizacion(datos_cotizacion, datos_cliente, items):
    """
    Función principal para generar el PDF.
    """
    
    pdf = PDF('P', 'mm', 'Letter') # Portrait, milímetros, Carta
    pdf.add_page()
    
    # --- Bloque de Título y Cliente ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"COTIZACION: {datos_cotizacion['folio']}", 0, 1, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"Fecha: {datos_cotizacion['fecha']}", 0, 1, 'L')
    pdf.cell(0, 6, f"Nombre: {datos_cliente['nombre']}", 0, 1, 'L')
    pdf.cell(0, 6, f"Compañía: {datos_cliente['compania']}", 0, 1, 'L')
    pdf.cell(0, 6, f"E-mail: {datos_cliente['email']}", 0, 1, 'L')
    pdf.ln(10)

    # --- Cabecera de la Tabla de Items ---
    col_widths = {'item': 10, 'cat': 35, 'desc': 85, 'qty': 15, 'unit': 25, 'sub': 25}
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(col_widths['item'], 7, 'Item', 1, 0, 'C', True)
    pdf.cell(col_widths['cat'], 7, 'Catalog #', 1, 0, 'C', True)
    pdf.cell(col_widths['desc'], 7, 'Description', 1, 0, 'C', True)
    pdf.cell(col_widths['qty'], 7, 'Qty', 1, 0, 'C', True)
    pdf.cell(col_widths['unit'], 7, 'Unit Price', 1, 0, 'C', True)
    pdf.cell(col_widths['sub'], 7, 'SubTotal', 1, 1, 'C', True)

    # --- Contenido de la Tabla (Items) ---
    pdf.set_font('Arial', '', 8)
    subtotal_general = 0
    moneda_str = datos_cotizacion['moneda']

    for i, item in enumerate(items):
        # Calcular altura necesaria para la descripción
        pdf.set_font('Arial', '', 8)
        desc_lines = pdf.multi_cell(col_widths['desc'], 6, item['desc'], border=0, split_only=True)
        line_height = 6
        total_height = len(desc_lines) * line_height

        # Dibujar celdas con la altura calculada
        pdf.cell(col_widths['item'], total_height, str(i + 1), 1, 0, 'C')
        pdf.cell(col_widths['cat'], total_height, item['catalogo'], 1, 0, 'L')
        
        # Guardar posición para la multicelda de descripción
        x_before_desc = pdf.get_x()
        y_before_desc = pdf.get_y()
        pdf.multi_cell(col_widths['desc'], line_height, item['desc'], 1, 'L')
        
        # Restaurar posición para las celdas restantes
        pdf.set_xy(x_before_desc + col_widths['desc'], y_before_desc)
        
        pdf.cell(col_widths['qty'], total_height, str(item['qty']), 1, 0, 'C')
        pdf.cell(col_widths['unit'], total_height, f"$ {item['precio']:.2f}", 1, 0, 'R')
        pdf.cell(col_widths['sub'], total_height, f"$ {item['subtotal']:.2f}", 1, 1, 'R')
        
        subtotal_general += item['subtotal']

    # --- Total ---
    pdf.set_font('Arial', 'B', 10)
    total_x_pos = col_widths['item'] + col_widths['cat'] + col_widths['desc'] + col_widths['qty'] + col_widths['unit']
    pdf.set_x(total_x_pos) # Alinea con las celdas de precio
    pdf.cell(col_widths['unit'], 8, f'SUBTOTAL({moneda_str})', 1, 0, 'R')
    pdf.cell(col_widths['sub'], 8, f'$ {subtotal_general:.2f}', 1, 1, 'R')
    pdf.ln(10)

    # --- Condiciones Comerciales ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, 'CONDICIONES COMERCIALES:', 0, 1, 'L')
    pdf.set_font('Arial', '', 8)
    pdf.multi_cell(0, 4, TERMINOS_COMERCIALES)

    # --- Salida ---
    nombre_archivo = f"COTIZACION-{datos_cotizacion['folio']}.pdf"
    try:
        pdf.output(nombre_archivo)
        print(f"\n¡PDF '{nombre_archivo}' generado con éxito!")

        # Opcional: Abrir el PDF automáticamente
        if sys.platform == "win32":
            os.startfile(nombre_archivo)
        elif sys.platform == "darwin": # macOS
            os.system(f"open {nombre_archivo}")
        else: # linux
            os.system(f"xdg-open {nombre_archivo}")
            
    except PermissionError:
        print(f"\nError: No se pudo escribir el archivo '{nombre_archivo}'.")
        print("Asegúrate de que el archivo no esté abierto en otro programa.")
    except Exception as e:
        print(f"No se pudo abrir el PDF automáticamente: {e}")