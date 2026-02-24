import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import TOKEN, USER_ID
# Importamos las funciones necesarias de database
from database import init_db, registrar_movimiento, obtener_resumen, registrar_ingreso_db, liquidar_deuda_db

# Configuración de logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DECORADOR DE SEGURIDAD ---
def solo_sajit(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != USER_ID:
            await update.message.reply_text("🚫 No tienes permiso para usar este bot.")
            return
        return await func(update, context)
    return wrapper

# --- COMANDOS ---

@solo_sajit
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola Sajit! Tu panel financiero está listo.\n\n"
        "Comandos:\n"
        "💰 /ingreso [monto] [detalle]\n"
        "💸 /gasto [monto] [cuenta] [detalle]\n"
        "_(Cuenta: 'efectivo' o nombre de tu tarjeta/persona)_\n"
        "💳 /pagar [monto] [cuenta]\n"
        "Comandos rápidos:\n"
        "🚌 /escuela - Registra tus $22 de transporte diario.\n"
        "📈 /saldo (Estado actual)"
    )

@solo_sajit
async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        detalle = " ".join(context.args[1:]) if len(context.args) > 1 else "Ingreso"
        registrar_ingreso_db(monto, detalle)
        await update.message.reply_text(f"✅ Recibido: ${monto:,.2f} en tu cuenta de rendimientos.")
    except:
        await update.message.reply_text("❌ Uso: /ingreso 6450 Quincena")

@solo_sajit
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        cuenta = context.args[1]
        detalle = " ".join(context.args[2:]) if len(context.args) > 2 else "Gasto"
        registrar_movimiento(monto, cuenta, "Varios", detalle)
        await update.message.reply_text(f"📝 Registrado: ${monto:,.2f} en {cuenta.capitalize()}.")
    except:
        await update.message.reply_text("❌ Uso: /gasto [monto] [efectivo/tarjeta] [detalle]")

@solo_sajit
async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        cuenta = context.args[1]
        liquidar_deuda_db(monto, cuenta)
        await update.message.reply_text(f"✅ Pagado: ${monto:,.2f} a {cuenta.capitalize()}. Se descontó de tu efectivo.")
    except:
        await update.message.reply_text("❌ Uso: /pagar [monto] [tarjeta/persona]")

@solo_sajit
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saldos = obtener_resumen()
    efectivo = saldos.get('Efectivo', 0)
    
    mensaje = "🏦 **ESTADO FINANCIERO**\n"
    mensaje += f"💰 **Dinero Disponible:** ${efectivo:,.2f}\n"
    mensaje += "_(Ganando intereses en tu cuenta principal)_\n\n"
    
    mensaje += "📝 **CUENTAS POR PAGAR (Deudas):**\n"
    deuda_total = 0
    hay_deudas = False
    for cuenta, monto in saldos.items():
        # Mostramos solo las cuentas que deben dinero (negativas)
        if cuenta != 'Efectivo' and monto < 0:
            mensaje += f"🔸 {cuenta}: ${abs(monto):,.2f}\n"
            deuda_total += abs(monto)
            hay_deudas = True
            
    if not hay_deudas:
        mensaje += "✅ Sin deudas pendientes.\n"
    else:
        mensaje += f"**Total Deuda:** ${deuda_total:,.2f}\n"
        
    ahorro_neto = efectivo - deuda_total
    mensaje += f"\n✨ **Ahorro Neto Real:** ${ahorro_neto:,.2f}"
    await update.message.reply_text(mensaje, parse_mode='Markdown')

@solo_sajit
async def escuela(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Definimos el monto fijo de tu gasto diario
    monto_fijo = 22.0
    # Usamos la función que ya tenemos en database.py
    registrar_movimiento(monto_fijo, "efectivo", "Transporte", "Gasto diario UPIITA")
    
    await update.message.reply_text(f"🚌 Gasto de la escuela registrado: ${monto_fijo:,.2f} restados de tu efectivo.")

# --- EJECUCIÓN ---

if __name__ == '__main__':
    # Inicializamos la DB
    init_db()
    
    # Construimos la aplicación
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Agregamos los manejadores (Aquí corregí los nombres)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingreso", ingreso))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("pagar", pagar))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("escuela", escuela))
    
    print("🚀 Bot financiero de Sajit iniciado...")
    app.run_polling()