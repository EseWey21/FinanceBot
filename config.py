# config.py
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
# Convertimos a int porque os.getenv siempre devuelve texto (string)
USER_ID = int(os.getenv("SAJIT_USER_ID"))
DB_NAME = os.getenv("DATABASE_NAME")