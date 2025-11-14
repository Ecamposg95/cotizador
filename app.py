# --- app.py ---
# (Este es el código del SERVIDOR WEB)

from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import db_manager
import pdf_generator
from datetime import datetime
import os

# Configuración de Flask
app = Flask(__name__)
app.secret_key = 'tu_llave_secreta_aqui' # Necesario para 'flash' messages
DB_NAME = "cotizaciones.db"

# --- Configuración de Base de Datos ---
def get_db():
    conn = db_manager.crear_conexion(DB_NAME)
    db_manager.setup_database(conn) # Asegura que las tablas existan
    return conn

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    """Muestra la página principal con el formulario."""
    conn = get_db()
    # Estas funciones DEBEN existir en db_manager.py
    clientes = db_manager.buscar_cliente_por_nombre(conn, '') # Trae todos
    productos = db_manager.get_all_productos(conn) # ¡Necesitamos agregar esta función!
    conn.close()
    return render_template('index.html', clientes=clientes, productos=productos)

@app.route('/generar_pdf', methods=['POST'])
def generar_cotizacion_pdf():
    """Recibe los datos del formulario, guarda y genera el PDF."""
    
    conn = get_db()
    try:
        # --- 1. Obtener datos del formulario ---
        datos = request.form

        # --- 2. Obtener o crear Cliente ---
        if datos['cliente_id'] == 'nuevo':
            cliente_id = db_manager.crear_cliente(conn, datos['nuevo_cliente_nombre'], datos['nuevo_cliente_compania'], datos['nuevo_cliente_email'])
            cliente = {'id': cliente_id, 'nombre': datos['nuevo_cliente_nombre'], 'compania': datos['nuevo_cliente_compania'], 'email': datos['nuevo_cliente_email']}
        else:
            cliente_id = int(datos['cliente_id'])
            cliente_db = db_manager.buscar_cliente_por_id(conn, cliente_id) # ¡Necesitamos agregar esta función!
            cliente = dict(cliente_db)
            
        # --- 3. Obtener o crear Producto (simplificado a 1 producto) ---
        if datos['producto_id'] == 'nuevo':
            producto_id = db_manager.crear_producto(conn, datos['nuevo_catalogo'], datos['nuevo_descripcion'], float(datos['nuevo_precio']), datos['nuevo_moneda'])
            producto = {'id': producto_id, 'catalogo': datos['nuevo_catalogo'], 'descripcion': datos['nuevo_descripcion'], 'precio_base': float(datos['nuevo_precio']), 'moneda_base': datos['nuevo_moneda']}
        else:
            producto_id = int(datos['producto_id'])
            producto_db = db_manager.buscar_producto_por_id(conn, producto_id) # ¡Necesitamos agregar esta función!
            producto = dict(producto_db)

        # --- 4. Lógica de Cálculo de Precios ---
        moneda_cot = datos['moneda_cotizacion']
        tc_dia = float(datos.get('tipo_cambio', 1.0) or 1.0)
        qty = int(datos['cantidad'])

        precio_convertido = 0.0
        if moneda_cot == 'USD':
            precio_convertido = producto['precio_base'] / tc_dia if producto['moneda_base'] == 'MXN' else producto['precio_base']
        else: # MXN
            precio_convertido = producto['precio_base'] * tc_dia if producto['moneda_base'] == 'USD' else producto['precio_base']
            
        subtotal_item = precio_convertido * qty
        
        # --- 5. Crear el item para el PDF y la DB ---
        items_para_pdf_y_db = [{
            'producto_id': producto['id'],
            'qty': qty,
            'catalogo': producto['catalogo'],
            'desc': producto['descripcion'],
            'precio': precio_convertido,
            'subtotal': subtotal_item
        }]
        
        # --- 6. Guardar en Base de Datos ---
        fecha_hoy = datetime.now()
        folio_base = db_manager.crear_cotizacion_completa(
            conn,
            cliente_id=cliente['id'],
            total=subtotal_item, # Total es solo este item por ahora
            moneda=moneda_cot,
            tipo_cambio=tc_dia,
            fecha=fecha_hoy,
            items=items_para_pdf_y_db
        )
        
        folio_str = f"C-{fecha_hoy.year}{folio_base:04d}"
        
        # --- 7. Generar el PDF ---
        datos_cotizacion = {
            'folio': folio_str,
            'fecha': fecha_hoy.strftime('%d de %B de %Y'),
            'moneda': moneda_cot
        }
        datos_cliente_pdf = {
            'nombre': cliente['nombre'],
            'compania': cliente['compania'],
            'email': cliente['email']
        }
        
        # Usamos la misma función, que ya guarda el archivo
        pdf_generator.crear_pdf_cotizacion(datos_cotizacion, datos_cliente_pdf, items_para_pdf_y_db)
        nombre_archivo = f"COTIZACION-{folio_str}.pdf"
        
        # Enviar el archivo al usuario para descarga
        return send_file(nombre_archivo, as_attachment=True)

    except Exception as e:
        flash(f"Error al generar la cotización: {e}")
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    # Esto permite ejecutar con 'python app.py'
    # Establecer localización
    try:
        import locale
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
        except:
            print("Advertencia: No se pudo configurar la localización a español.")
            
    app.run(debug=True, host='0.0.0.0', port=5000) # debug=True te ayuda a ver errores