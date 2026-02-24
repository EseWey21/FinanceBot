# FinanceBot (Telegram)

Bot de Telegram para registrar ingresos/gastos, manejar deudas (tarjetas/personas) y consultar saldo usando SQLite.

## Requisitos

- Raspberry Pi OS (Debian) con **Python 3.10+**
- Un bot de Telegram (token de @BotFather)
- Tu `user_id` de Telegram (para restringir el acceso)

## Instalación en Raspberry Pi

### 1) Clonar el proyecto

```bash
cd ~
git clone https://github.com/EseWey21/FinanceBot.git
cd FinanceBot
```

### 2) Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 3) Crear entorno virtual e instalar dependencias Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Configurar variables de entorno (.env)

Crea un archivo `.env` dentro de esta carpeta (`FinanceBot/`) con este contenido:

```env
TELEGRAM_TOKEN=123456789:ABCDEF_TU_TOKEN
SAJIT_USER_ID=123456789
DATABASE_NAME=financebot.db
```

Notas:
- `SAJIT_USER_ID` debe ser numérico (en [config.py](config.py) se convierte a `int`).
- `DATABASE_NAME` puede ser un nombre de archivo local (`financebot.db`).

### 5) Ejecutar el bot

```bash
source .venv/bin/activate
python3 main.py
```

Al iniciar, se crea/actualiza la base de datos SQLite automáticamente.

## Comandos del bot

- `/start` — muestra ayuda
- `/ingreso [monto] [detalle]`
  - Ejemplo: `/ingreso 6450 Quincena`
- `/gasto [monto] [cuenta] [detalle]`
  - Ejemplo: `/gasto 250 nu Uber`
  - `cuenta`: `efectivo` o el nombre de tu tarjeta/persona (se considera deuda si no es efectivo/débito/nómina)
- `/pagar [monto] [cuenta]`
  - Ejemplo: `/pagar 1000 nu`
- `/saldo` — muestra dinero disponible, deudas y ahorro neto

## Estructura rápida

- [main.py](main.py): handlers de Telegram y comandos
- [database.py](database.py): SQLite (movimientos, saldos)
- [config.py](config.py): carga variables desde `.env`

## Solución de problemas

- Si al arrancar falla por variables faltantes: revisa que exista `.env` y que `TELEGRAM_TOKEN`, `SAJIT_USER_ID`, `DATABASE_NAME` estén definidos.
- Si `SAJIT_USER_ID` no es número, Python lanzará error al convertirlo a `int`.
- Para ver logs más verbosos, cambia el `level` en `logging.basicConfig(...)` en [main.py](main.py).

## (Opcional) Ejecutarlo como servicio (systemd)

Si quieres que arranque al prender la Raspberry:

1) Crea un servicio:

```bash
sudo nano /etc/systemd/system/financebot.service
```

2) Contenido (ajusta `User` y rutas):

```ini
[Unit]
Description=FinanceBot Telegram
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/FinanceBot
EnvironmentFile=/home/pi/FinanceBot/.env
ExecStart=/home/pi/FinanceBot/.venv/bin/python /home/pi/FinanceBot/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3) Activar y arrancar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now financebot
sudo systemctl status financebot --no-pager
```

Ver logs:

```bash
journalctl -u financebot -f
```
