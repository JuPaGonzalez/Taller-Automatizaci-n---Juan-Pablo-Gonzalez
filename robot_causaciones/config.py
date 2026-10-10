import os
from pathlib import Path
from dotenv import load_dotenv

DIR_BASE = Path(__file__).resolve().parent
load_dotenv(DIR_BASE / ".env")

PORTAL_URL = os.getenv("PORTAL_URL", "http://127.0.0.1:8020").rstrip("/")
PORTAL_USUARIO = os.getenv("PORTAL_USUARIO", "operador.rpa")
PORTAL_CLAVE = os.getenv("PORTAL_CLAVE", "CxpSicof2026")
BOT_HEADLESS = os.getenv("BOT_HEADLESS", "true").strip().lower() in ("true", "1", "yes")

DIR_DATOS = DIR_BASE / "datos"
ARCHIVO_POR_RADICAR = DIR_DATOS / "por_radicar.xlsx"

DIR_SALIDA = DIR_BASE / "salida"
ARCHIVO_LOG = DIR_SALIDA / "bot.log"
ARCHIVO_RESULTADOS = DIR_SALIDA / "resultados.xlsx"
DIR_EVIDENCIAS = DIR_SALIDA / "evidencias"
