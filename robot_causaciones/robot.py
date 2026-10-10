import logging
import time
from pathlib import Path
from playwright.sync_api import Page

import config
from excepciones import ExcepcionNegocio, ExcepcionSistema
from modelo import FacturaEntrada, ResultadoFactura
from paginas.login import PaginaLogin
from paginas.consulta import PaginaConsulta
from paginas.nueva_causacion import PaginaNuevaCausacion
from paginas.revision import PaginaRevision


logger = logging.getLogger("robot_causaciones")


class RobotCausaciones:
    def __init__(self, pagina: Page) -> None:
        self.pagina = pagina
        self.pag_login = PaginaLogin(pagina, config.PORTAL_URL)
        self.pag_consulta = PaginaConsulta(pagina, config.PORTAL_URL)
        self.pag_nueva = PaginaNuevaCausacion(pagina, config.PORTAL_URL)
        self.pag_revision = PaginaRevision(pagina, config.PORTAL_URL)

    def iniciar(self) -> None:
        """Asegura la autenticación en el portal SICOF."""
        self.pag_login.iniciar_sesion(config.PORTAL_USUARIO, config.PORTAL_CLAVE)

    def procesar_factura(self, factura: FacturaEntrada) -> ResultadoFactura:
        """
        Procesa una factura individual contra SICOF:
        1. Consulta si ya existe (Idempotencia).
        2. Si no existe, intenta registrarla con hasta 3 reintentos ante fallas de sistema.
        3. Maneja rechazos de negocio sin reintentar.
        """
        # 1. Consulta previa de causación (Idempotencia)
        causacion_existente = self.pag_consulta.buscar_causacion_existente(factura.nit, factura.factura)
        if causacion_existente:
            logger.info(
                f"Factura {factura.factura} (NIT {factura.nit}) procesada: YA_CAUSADA - {causacion_existente}"
            )
            return ResultadoFactura(
                id_lista=factura.id_lista,
                factura=factura.factura,
                nit=factura.nit,
                estado="YA_CAUSADA",
                causacion=causacion_existente,
                detalle="",
            )

        # 2. Ciclo de registro con reintentos para fallas de sistema
        max_intentos = 3
        ultimo_error_sistema = ""

        for intento in range(1, max_intentos + 1):
            try:
                # Paso 1: Llenar formulario y continuar
                self.pag_nueva.llenar_y_continuar(
                    nit=factura.nit,
                    factura=factura.factura,
                    fecha_factura=factura.fecha_factura,
                    valor=factura.valor,
                    centro_costo=factura.centro_costo,
                )

                # Paso 2: Confirmar causación
                numero_cxp = self.pag_revision.confirmar()

                logger.info(
                    f"Factura {factura.factura} (NIT {factura.nit}) procesada: CAUSADA - {numero_cxp}"
                )
                return ResultadoFactura(
                    id_lista=factura.id_lista,
                    factura=factura.factura,
                    nit=factura.nit,
                    estado="CAUSADA",
                    causacion=numero_cxp,
                    detalle="",
                )

            except ExcepcionNegocio as en:
                # Los rechazos de negocio o alertas no se reintentan
                detalle_rechazo = str(en)
                logger.info(
                    f"Factura {factura.factura} (NIT {factura.nit}) procesada: RECHAZADA - {detalle_rechazo}"
                )
                return ResultadoFactura(
                    id_lista=factura.id_lista,
                    factura=factura.factura,
                    nit=factura.nit,
                    estado="RECHAZADA",
                    causacion="",
                    detalle=detalle_rechazo,
                )

            except ExcepcionSistema as es:
                ultimo_error_sistema = str(es)
                if intento < max_intentos:
                    logger.warning(
                        f"Reintento {intento}/{max_intentos} para factura {factura.factura} (NIT {factura.nit}): {ultimo_error_sistema}"
                    )
                    time.sleep(1)
                else:
                    # Agotados los 3 intentos, capturar evidencia y marcar falla de sistema
                    config.DIR_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
                    ruta_evidencia = config.DIR_EVIDENCIAS / f"falla_{factura.factura}_{factura.nit}.png"
                    try:
                        self.pagina.screenshot(path=str(ruta_evidencia))
                    except Exception:
                        pass

                    logger.error(
                        f"Factura {factura.factura} (NIT {factura.nit}) procesada: FALLA_SISTEMA - {ultimo_error_sistema}"
                    )
                    return ResultadoFactura(
                        id_lista=factura.id_lista,
                        factura=factura.factura,
                        nit=factura.nit,
                        estado="FALLA_SISTEMA",
                        causacion="",
                        detalle=ultimo_error_sistema,
                    )

        return ResultadoFactura(
            id_lista=factura.id_lista,
            factura=factura.factura,
            nit=factura.nit,
            estado="FALLA_SISTEMA",
            causacion="",
            detalle=ultimo_error_sistema,
        )
