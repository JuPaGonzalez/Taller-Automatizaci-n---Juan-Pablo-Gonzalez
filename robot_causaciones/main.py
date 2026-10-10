import logging
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

import config
from gestor_excel import leer_facturas_por_radicar, guardar_resultados
from modelo import ResultadoFactura
from robot import RobotCausaciones


def configurar_logging() -> logging.Logger:
    """Configura el logging para escribir tanto en salida/bot.log como en consola."""
    config.DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("robot_causaciones")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formato = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Manejador de archivo para salida/bot.log
    manejador_archivo = logging.FileHandler(config.ARCHIVO_LOG, mode="a", encoding="utf-8")
    manejador_archivo.setFormatter(formato)
    manejador_archivo.setLevel(logging.INFO)
    logger.addHandler(manejador_archivo)

    # Manejador de consola
    manejador_consola = logging.StreamHandler(sys.stdout)
    manejador_consola.setFormatter(formato)
    manejador_consola.setLevel(logging.INFO)
    logger.addHandler(manejador_consola)

    return logger


def main() -> None:
    logger = configurar_logging()
    logger.info("Iniciando ejecución del Robot de Causaciones SICOF")

    if not config.ARCHIVO_POR_RADICAR.exists():
        logger.error(f"No se encontró el archivo de entrada: {config.ARCHIVO_POR_RADICAR}")
        sys.exit(1)

    items = leer_facturas_por_radicar(config.ARCHIVO_POR_RADICAR)
    logger.info(f"Se encontraron {len(items)} facturas para procesar en {config.ARCHIVO_POR_RADICAR.name}")

    resultados: list[ResultadoFactura] = []

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=config.BOT_HEADLESS)
        contexto = navegador.new_context()
        pagina = contexto.new_page()

        robot = RobotCausaciones(pagina)
        try:
            robot.iniciar()
        except Exception as e:
            logger.error(f"Error crítico al conectar con SICOF: {e}")
            navegador.close()
            sys.exit(1)

        for factura_entrada, resultado_previo in items:
            if resultado_previo is not None:
                # Factura rechazada en validaciones previas al ingreso a SICOF
                logger.info(
                    f"Factura {resultado_previo.factura} (NIT {resultado_previo.nit}) procesada: "
                    f"RECHAZADA - {resultado_previo.detalle}"
                )
                resultados.append(resultado_previo)
            elif factura_entrada is not None:
                resultado = robot.procesar_factura(factura_entrada)
                resultados.append(resultado)

        contexto.close()
        navegador.close()

    # Guardar archivo salida/resultados.xlsx
    guardar_resultados(resultados, config.ARCHIVO_RESULTADOS)
    logger.info(f"Resultados guardados exitosamente en: {config.ARCHIVO_RESULTADOS}")

    # Resumen
    conteo_causadas = sum(1 for r in resultados if r.estado == "CAUSADA")
    conteo_ya_causadas = sum(1 for r in resultados if r.estado == "YA_CAUSADA")
    conteo_rechazadas = sum(1 for r in resultados if r.estado == "RECHAZADA")
    conteo_fallas = sum(1 for r in resultados if r.estado == "FALLA_SISTEMA")

    logger.info(
        f"Lote finalizado. Resumen: CAUSADA={conteo_causadas}, "
        f"YA_CAUSADA={conteo_ya_causadas}, RECHAZADA={conteo_rechazadas}, "
        f"FALLA_SISTEMA={conteo_fallas}"
    )


if __name__ == "__main__":
    main()
