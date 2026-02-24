import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import TOKEN, USER_ID
# Importamos las funciones necesarias de database
from database import (init_db, registrar_movimiento, obtener_resumen, 
                      registrar_ingreso_db, liquidar_deuda_db, 
                      registrar_pago_recibido_db, registrar_cuenta_por_cobrar,
                      registrar_deuda_pasivo)
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
        "👋 ¡Hola Sajit! Tu control financiero total está listo:\n\n"
        "💰 **GESTIÓN DE DINERO**\n"
        "• /ingreso [monto] [detalle] - Dinero que entra a tu cuenta.\n"
        "• /gasto [monto] [detalle] - Gasto rápido (resta de tu efectivo).\n"
        "• /saldo - Tu balance real, deudas y préstamos.\n\n"
        
        "💳 **CUENTAS POR PAGAR (Tus deudas)**\n"
        "• /deuda [monto] [nombre] [detalle] - Lo que debes a tarjetas o personas.\n"
        "• /pagar [monto] [nombre] - Liquidar tus deudas con tu efectivo.\n\n"
        
        "🤝 **CUENTAS POR COBRAR (Te deben)**\n"
        "• /debe [monto] [persona] [detalle] - Dinero que prestaste a alguien.\n"
        "• /pago [monto] [persona] - Cuando te devuelven dinero (suma a tu efectivo).\n\n"
        
        "🚌 **ATAJOS DE TRANSPORTE**\n"
        "• /escuela ($22) | /metro ($5) | /camion ($8.5)\n"
        "• /rtp ($2) | /directo ($20)",
        parse_mode='Markdown'
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
        # Ahora el detalle es todo lo que sigue después del monto
        detalle = " ".join(context.args[1:]) if len(context.args) > 1 else "Gasto"
        
        # Forzamos que siempre sea a "Efectivo"
        registrar_movimiento(monto, "Efectivo", "Varios", detalle)
        await update.message.reply_text(f"💸 Restados ${monto:,.2f} de tu efectivo por: {detalle}.")
    except:
        await update.message.reply_text("❌ Uso: /gasto [monto] [detalle]")

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
    mensaje += f"💰 **Dinero Disponible:** ${efectivo:,.2f}\n\n"
    
    cuentas_pagar = ""
    cuentas_cobrar = ""
    deuda_total = 0
    cobrar_total = 0

    for cuenta, monto in saldos.items():
        if cuenta == 'Efectivo' or monto == 0: continue
        if monto < 0:
            cuentas_pagar += f"🔸 {cuenta}: ${abs(monto):,.2f}\n"
            deuda_total += abs(monto)
        else:
            cuentas_cobrar += f"🔹 {cuenta}: ${monto:,.2f}\n"
            cobrar_total += monto

    if cuentas_cobrar:
        mensaje += "📈 **CUENTAS POR COBRAR:**\n" + cuentas_cobrar + f"**Total a favor:** ${cobrar_total:,.2f}\n\n"
    if cuentas_pagar:
        mensaje += "📉 **CUENTAS POR PAGAR:**\n" + cuentas_pagar + f"**Total deuda:** ${deuda_total:,.2f}\n\n"
        
    ahorro_neto = efectivo - deuda_total + cobrar_total
    mensaje += f"✨ **Ahorro Neto Real:** ${ahorro_neto:,.2f}"
    await update.message.reply_text(mensaje, parse_mode='Markdown')

@solo_sajit
async def escuela(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Definimos el monto fijo de tu gasto diario
    monto_fijo = 22.0
    # Usamos la función que ya tenemos en database.py
    registrar_movimiento(monto_fijo, "efectivo", "Transporte", "Gasto diario UPIITA")
    
    await update.message.reply_text(f"🚌 Gasto de la escuela registrado: ${monto_fijo:,.2f} restados de tu efectivo.")

@solo_sajit
async def deuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        nombre = context.args[1] # Ej: Nu, BBVA o Juan
        detalle = " ".join(context.args[2:]) if len(context.args) > 2 else "Deuda"

        registrar_deuda_pasivo(monto, nombre, detalle)
        await update.message.reply_text(f"💳 Anotada deuda de ${monto:,.2f} en {nombre.capitalize()}.")
    except:
        await update.message.reply_text("❌ Uso: /deuda 500 Nu super")

@solo_sajit
async def metro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    monto = 5.0
    registrar_movimiento(monto, "Efectivo", "Transporte", "Metro")
    await update.message.reply_text(f"🚇 Metro registrado: ${monto:,.2f} restados.")

@solo_sajit
async def camion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    monto = 8.5
    registrar_movimiento(monto, "Efectivo", "Transporte", "Camión")
    await update.message.reply_text(f"🚌 Camión registrado: ${monto:,.2f} restados.")

@solo_sajit
async def rtp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    monto = 2.0
    registrar_movimiento(monto, "Efectivo", "Transporte", "RTP")
    await update.message.reply_text(f"🚌 RTP registrado: ${monto:,.2f} restados.")

@solo_sajit
async def directo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    monto = 20.0
    registrar_movimiento(monto, "Efectivo", "Transporte", "Directo / Micro")
    await update.message.reply_text(f"🚐 Directo registrado: ${monto:,.2f} restados.")

@solo_sajit
async def debe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        persona = context.args[1]
        detalle = " ".join(context.args[2:]) if len(context.args) > 2 else "Préstamo"
        registrar_cuenta_por_cobrar(monto, persona, detalle)
        await update.message.reply_text(f"💰 Registro: {persona.capitalize()} ahora te debe ${monto:,.2f}.")
    except:
        await update.message.reply_text("❌ Uso: /debe [monto] [persona] [detalle]")

@solo_sajit
async def pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        persona = context.args[1]
        registrar_pago_recibido_db(monto, persona)
        await update.message.reply_text(f"✅ ¡Dinero recibido! Se sumaron ${monto:,.2f} a tu disponible.")
    except:
        await update.message.reply_text("❌ Uso: /pago [monto] [persona]")

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
    app.add_handler(CommandHandler("deuda", deuda))
    app.add_handler(CommandHandler("metro", metro))
    app.add_handler(CommandHandler("camion", camion))
    app.add_handler(CommandHandler("rtp", rtp))
    app.add_handler(CommandHandler("directo", directo))
    app.add_handler(CommandHandler("debe", debe))
    app.add_handler(CommandHandler("pago", pago))
    print("🚀 Bot financiero de Sajit iniciado...")
    app.run_polling()