import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from config import TOKEN, USER_ID
from database import init_db, registrar_movimiento, obtener_resumen

# Configuración de logs para ver errores en la terminal
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
        "👋 ¡Hola Sajit! Tu gestor financiero está listo.\n\n"
        "Comandos básicos:\n"
        "💰 /ingreso [monto] [detalle]\n"
        "💸 /gasto [monto] [detalle]\n"
        "💳 /tc [monto] [detalle] (Gasto con tarjeta)\n"
        "📈 /balance (Ver tus cuentas)\n"
        "🚗 /metas (Rumbo al Nissan March)"
    )

@solo_sajit
async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        detalle = " ".join(context.args[1:]) if len(context.args) > 1 else "Ingreso general"
        
        registrar_movimiento(monto, 'INGRESO', 'Efectivo', 'Nomina', detalle)
        await update.message.reply_text(f"✅ Recibido: ${monto:,.2f} en Efectivo.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Uso correcto: /ingreso 6450 Nomina IBM")

@solo_sajit
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        detalle = " ".join(context.args[1:]) if len(context.args) > 1 else "Gasto general"
        
        registrar_movimiento(monto, 'GASTO', 'Efectivo', 'Varios', detalle)
        await update.message.reply_text(f"💸 Registrado: -${monto:,.2f} de tu Efectivo.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Uso correcto: /gasto 150 Comida")

@solo_sajit
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saldos = obtener_resumen()
    
    mensaje = "📊 **RESUMEN DE CUENTAS**\n\n"
    total_disponible = 0
    for cuenta, monto in saldos.items():
        # La tarjeta la mostramos aparte para no sumarla como "dinero que tienes"
        if cuenta == 'TC':
            mensaje += f"💳 Deuda Tarjeta: ${abs(monto):,.2f}\n"
        else:
            mensaje += f"🔹 {cuenta}: ${monto:,.2f}\n"
            total_disponible += monto
            
    mensaje += f"\n💰 **Total Neto:** ${total_disponible + saldos.get('TC', 0):,.2f}"
    await update.message.reply_text(mensaje, parse_mode='Markdown')

@solo_sajit
async def metas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saldos = obtener_resumen()
    # Sumamos lo que tienes en Revolut y Nu
    ahorro_actual = saldos.get('Revolut', 0) + saldos.get('Nu', 0)
    meta_march = 90000
    porcentaje = (ahorro_actual / meta_march) * 100
    faltante = meta_march - ahorro_actual
    
    progreso = "▓" * int(porcentaje // 10) + "░" * (10 - int(porcentaje // 10))
    
    mensaje = (
        f"🚗 **META: NISSAN MARCH**\n"
        f"Progreso: {progreso} {porcentaje:.1f}%\n\n"
        f"💰 Llevas: ${ahorro_actual:,.2f}\n"
        f"🏁 Faltan: ${max(0, faltante):,.2f}\n"
    )
    
    if ahorro_actual >= meta_march:
        mensaje += "\n🥳 ¡LO LOGRASTE! Ya puedes ir por el carro."
    else:
        mensaje += "\n💡 ¡Cada peso cuenta, sigue así!"
        
    await update.message.reply_text(mensaje)

# --- EJECUCIÓN ---

if __name__ == '__main__':
    # Inicializamos la DB
    init_db()
    
    # Construimos la aplicación
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Agregamos los manejadores
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingreso", ingreso))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("metas", metas))
    
    print("🚀 Bot financiero de Sajit iniciado...")
    app.run_polling()