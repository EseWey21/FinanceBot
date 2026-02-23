# database.py
import sqlite3
from config import DB_NAME

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla para el historial de movimientos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            monto REAL NOT NULL,
            tipo TEXT,          -- 'INGRESO', 'GASTO', 'TRASPASO', 'INTERES'
            cuenta TEXT,        -- 'Efectivo', 'Revolut', 'Nu', 'TC'
            categoria TEXT,     -- 'Nomina', 'Transporte', 'Comida', etc.
            descripcion TEXT
        )
    ''')
    
    # Tabla para saldos actuales (para consultas rápidas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saldos (
            cuenta TEXT PRIMARY KEY,
            monto REAL DEFAULT 0
        )
    ''')
    
    # Inicializar cuentas si no existen
    cuentas = [('Efectivo',), ('Revolut',), ('Nu',), ('TC',)]
    cursor.executemany('INSERT OR IGNORE INTO saldos (cuenta) VALUES (?)', cuentas)
    
    conn.commit()
    conn.close()

def registrar_movimiento(monto, tipo, cuenta, categoria, desc=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Registrar en el historial
    cursor.execute('''
        INSERT INTO movimientos (monto, tipo, cuenta, categoria, descripcion)
        VALUES (?, ?, ?, ?, ?)
    ''', (monto, tipo, cuenta, categoria, desc))
    
    # 2. Actualizar el saldo de la cuenta
    # Si es gasto o pago de TC, restamos. Si es ingreso o interés, sumamos.
    if tipo in ['GASTO', 'TC']:
        cursor.execute('UPDATE saldos SET monto = monto - ? WHERE cuenta = ?', (monto, cuenta))
    elif tipo in ['INGRESO', 'INTERES']:
        cursor.execute('UPDATE saldos SET monto = monto + ? WHERE cuenta = ?', (monto, cuenta))
        
    conn.commit()
    conn.close()

def obtener_resumen():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT cuenta, monto FROM saldos')
    resumen = cursor.fetchall() # Retorna una lista de tuplas [('Efectivo', 500), ...]
    conn.close()
    return dict(resumen)