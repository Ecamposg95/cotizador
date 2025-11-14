# --- db_manager.py ---
# (Versión completa para la App Web)

import sqlite3

def crear_conexion(db_file):
    """Crea una conexión a la base de datos SQLite"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row # Para acceder a los datos por nombre de columna
        conn.execute("PRAGMA foreign_keys = ON") # Importante para integridad
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def setup_database(conn):
    """Crea las tablas si no existen"""
    sql_clientes = """
    CREATE TABLE IF NOT EXISTS Clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        compania TEXT,
        email TEXT
    );"""
    
    sql_productos = """
    CREATE TABLE IF NOT EXISTS Productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_catalogo TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        precio_base REAL NOT NULL,
        moneda_base TEXT NOT NULL CHECK(moneda_base IN ('USD', 'MXN'))
    );"""
    
    sql_cotizaciones = """
    CREATE TABLE IF NOT EXISTS Cotizaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        fecha_creacion TEXT NOT NULL,
        total REAL NOT NULL,
        moneda_cotizada TEXT NOT NULL,
        tipo_cambio_dia REAL DEFAULT 1.0,
        estado TEXT NOT NULL DEFAULT 'Pendiente',
        FOREIGN KEY (cliente_id) REFERENCES Clientes (id)
    );"""
    
    sql_cotizacion_detalle = """
    CREATE TABLE IF NOT EXISTS Cotizacion_Detalle (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cotizacion_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario_final REAL NOT NULL,
        FOREIGN KEY (cotizacion_id) REFERENCES Cotizaciones (id) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES Productos (id)
    );"""
    
    try:
        c = conn.cursor()
        c.execute(sql_clientes)
        c.execute(sql_productos)
        c.execute(sql_cotizaciones)
        c.execute(sql_cotizacion_detalle)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al crear tablas: {e}")

# --- Funciones CRUD Clientes ---

def crear_cliente(conn, nombre, compania, email):
    sql = "INSERT INTO Clientes(nombre, compania, email) VALUES(?, ?, ?)"
    cur = conn.cursor()
    cur.execute(sql, (nombre, compania, email))
    conn.commit()
    return cur.lastrowid

def buscar_cliente_por_nombre(conn, termino):
    sql = "SELECT * FROM Clientes WHERE nombre LIKE ? OR compania LIKE ?"
    cur = conn.cursor()
    cur.execute(sql, (f'%{termino}%', f'%{termino}%'))
    filas = cur.fetchall()
    return [dict(fila) for fila in filas]

def buscar_cliente_por_id(conn, cliente_id):
    """Busca un cliente específico por su ID."""
    sql = "SELECT * FROM Clientes WHERE id = ?"
    cur = conn.cursor()
    cur.execute(sql, (cliente_id,))
    fila = cur.fetchone()
    return dict(fila) if fila else None

# --- Funciones CRUD Productos ---

def crear_producto(conn, catalogo, desc, precio, moneda):
    sql = "INSERT INTO Productos(numero_catalogo, descripcion, precio_base, moneda_base) VALUES(?, ?, ?, ?)"
    cur = conn.cursor()
    cur.execute(sql, (catalogo, desc, precio, moneda))
    conn.commit()
    return cur.lastrowid

def buscar_producto_por_catalogo(conn, catalogo):
    sql = "SELECT * FROM Productos WHERE numero_catalogo = ?"
    cur = conn.cursor()
    cur.execute(sql, (catalogo,))
    fila = cur.fetchone()
    return dict(fila) if fila else None

def buscar_producto_por_id(conn, producto_id):
    """Busca un producto específico por su ID."""
    sql = "SELECT * FROM Productos WHERE id = ?"
    cur = conn.cursor()
    cur.execute(sql, (producto_id,))
    fila = cur.fetchone()
    return dict(fila) if fila else None

def get_all_productos(conn):
    """Obtiene todos los productos para el dropdown."""
    sql = "SELECT * FROM Productos ORDER BY numero_catalogo"
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return [dict(fila) for fila in filas]

def check_productos_mxn(conn):
    """Verifica si hay algún producto en MXN, para saber si pedir TC"""
    sql = "SELECT 1 FROM Productos WHERE moneda_base = 'MXN' LIMIT 1"
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchone() is not None

# --- Funciones CRUD Cotizaciones ---

def crear_cotizacion_completa(conn, cliente_id, total, moneda, tipo_cambio, fecha, items):
    """
    Guarda la cotización y sus detalles en una transacción.
    """
    cur = conn.cursor()
    try:
        cur.execute("BEGIN TRANSACTION")
        
        # 1. Insertar la cotización principal
        sql_cot = """
        INSERT INTO Cotizaciones (cliente_id, fecha_creacion, total, moneda_cotizada, tipo_cambio_dia)
        VALUES (?, ?, ?, ?, ?)
        """
        cur.execute(sql_cot, (cliente_id, fecha.isoformat(), total, moneda, tipo_cambio))
        
        cotizacion_id = cur.lastrowid
        
        # 2. Insertar los detalles
        sql_detalle = """
        INSERT INTO Cotizacion_Detalle (cotizacion_id, producto_id, cantidad, precio_unitario_final)
        VALUES (?, ?, ?, ?)
        """
        for item in items:
            cur.execute(sql_detalle, (cotizacion_id, item['producto_id'], item['qty'], item['precio']))
        
        cur.execute("COMMIT")
        return cotizacion_id
        
    except sqlite3.Error as e:
        print(f"Error en la transacción: {e}")
        cur.execute("ROLLBACK")
        return None