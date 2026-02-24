# database.py
import sqlite3
from config import DB_NAME

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            monto REAL NOT NULL,
            tipo TEXT,          -- 'INGRESO', 'GASTO_REAL', 'GASTO_CREDITO', 'PAGO_DEUDA'
            cuenta TEXT,        -- 'Efectivo', 'Nu', 'BBVA', etc.
            categoria TEXT,
            descripcion TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saldos (
            cuenta TEXT PRIMARY KEY,
            monto REAL DEFAULT 0
        )
    ''')
    # Solo inicializamos la cuenta principal. Las tarjetas se crearán al usarlas.
    cursor.execute('INSERT OR IGNORE INTO saldos (cuenta, monto) VALUES ("Efectivo", 0)')
    conn.commit()
    conn.close()

def registrar_movimiento(monto, cuenta_input, categoria, desc=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cuenta = cuenta_input.strip().capitalize()
    # Si no es efectivo/debito, es crédito (pasivo)
    es_credito = cuenta not in ['Efectivo', 'Debito', 'Nomina']
    
    cursor.execute('INSERT OR IGNORE INTO saldos (cuenta, monto) VALUES (?, 0)', (cuenta,))
    
    if es_credito:
        # Aumenta la deuda (saldo más negativo)
        cursor.execute('INSERT INTO movimientos (monto, tipo, cuenta, categoria, descripcion) VALUES (?, "GASTO_CREDITO", ?, ?, ?)', (monto, cuenta, categoria, desc))
        cursor.execute('UPDATE saldos SET monto = monto - ? WHERE cuenta = ?', (monto, cuenta))
    else:
        # Resta de tu dinero real disponible
        cursor.execute('INSERT INTO movimientos (monto, tipo, cuenta, categoria, descripcion) VALUES (?, "GASTO_REAL", "Efectivo", ?, ?)', (monto, categoria, desc))
        cursor.execute('UPDATE saldos SET monto = monto - ? WHERE cuenta = "Efectivo"', (monto,))
    
    conn.commit()
    conn.close()

def registrar_ingreso_db(monto, desc):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO movimientos (monto, tipo, cuenta, categoria, descripcion) VALUES (?, "INGRESO", "Efectivo", "Nomina", ?)', (monto, desc))
    cursor.execute('UPDATE saldos SET monto = monto + ? WHERE cuenta = "Efectivo"', (monto,))
    conn.commit()
    conn.close()

def liquidar_deuda_db(monto, cuenta_deuda):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cuenta = cuenta_deuda.strip().capitalize()
    # Resta de efectivo y suma a la deuda (la acerca a cero)
    cursor.execute('UPDATE saldos SET monto = monto - ? WHERE cuenta = "Efectivo"', (monto,))
    cursor.execute('UPDATE saldos SET monto = monto + ? WHERE cuenta = ?', (monto, cuenta))
    cursor.execute('INSERT INTO movimientos (monto, tipo, cuenta, descripcion) VALUES (?, "PAGO_DEUDA", "Efectivo", ?)', (monto, f"Pago a {cuenta}"))
    conn.commit()
    conn.close()

def obtener_resumen():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT cuenta, monto FROM saldos')
    resumen = cursor.fetchall()
    conn.close()
    return dict(resumen)

def registrar_deuda_pasivo(monto, nombre_cuenta, desc):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cuenta = nombre_cuenta.strip().capitalize()
    
    # Asegura que la cuenta (ej. Nu o Juan) existe
    cursor.execute('INSERT OR IGNORE INTO saldos (cuenta, monto) VALUES (?, 0)', (cuenta,))
    
    # Aumenta la deuda (el saldo se vuelve más negativo)
    # No tocamos la cuenta "Efectivo"
    cursor.execute('UPDATE saldos SET monto = monto - ? WHERE cuenta = ?', (monto, cuenta))
    
    # Registramos el movimiento como GASTO_CREDITO
    cursor.execute('''
        INSERT INTO movimientos (monto, tipo, cuenta, categoria, descripcion) 
        VALUES (?, "GASTO_CREDITO", ?, "Deuda", ?)
    ''', (monto, cuenta, desc))
    
    conn.commit()
    conn.close()

def registrar_pago_recibido_db(monto, cuenta_persona):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cuenta = cuenta_persona.strip().capitalize()
    # 1. Sumamos el dinero a tu Efectivo disponible
    cursor.execute('UPDATE saldos SET monto = monto + ? WHERE cuenta = "Efectivo"', (monto,))
    # 2. Restamos de la cuenta de la persona (acercándola a cero)
    cursor.execute('UPDATE saldos SET monto = monto - ? WHERE cuenta = ?', (monto, cuenta))
    # 3. Registramos el historial
    cursor.execute('INSERT INTO movimientos (monto, tipo, cuenta, descripcion) VALUES (?, "PAGO_RECIBIDO", "Efectivo", ?)', (monto, f"Pago recibido de {cuenta}"))
    conn.commit()
    conn.close()

def registrar_cuenta_por_cobrar(monto, nombre_persona, desc):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cuenta = nombre_persona.strip().capitalize()
    # Asegura que la cuenta de la persona existe
    cursor.execute('INSERT OR IGNORE INTO saldos (cuenta, monto) VALUES (?, 0)', (cuenta,))
    # Aumenta el saldo a tu favor (saldo positivo)
    cursor.execute('UPDATE saldos SET monto = monto + ? WHERE cuenta = ?', (monto, cuenta))
    # Registramos el movimiento
    cursor.execute('INSERT INTO movimientos (monto, tipo, cuenta, categoria, descripcion) VALUES (?, "PRESTAMO_OTORGADO", ?, "Por Cobrar", ?)', (monto, cuenta, desc))
    conn.commit()
    conn.close()