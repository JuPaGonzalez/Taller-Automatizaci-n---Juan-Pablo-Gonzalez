import re
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from paginas.base import PaginaBase
from excepciones import ExcepcionNegocio, ExcepcionSistema


class PaginaRevision(PaginaBase):
    def confirmar(self) -> str:
        """
        Pulsa el botón 'Confirmar causación' y procesa la respuesta.
        - Si responde 'Servicio temporalmente no disponible' o SICOF-503: lanza ExcepcionSistema.
        - Si responde con un mensaje de alerta: lanza ExcepcionNegocio.
        - Si es exitoso: extrae y retorna el número de causación CXP-AAAA-NNNNNN.
        """
        try:
            btn_confirmar = self.pagina.get_by_role("button", name="Confirmar causación")
            btn_confirmar.wait_for(state="visible", timeout=10000)
            btn_confirmar.click()

            # Esperar a que la página cargue el resultado
            self.pagina.wait_for_load_state("domcontentloaded", timeout=10000)

            contenido = self.pagina.content()

            # Verificar si ocurrió el error de inestabilidad 503
            if "Servicio temporalmente no disponible" in contenido or "SICOF-503" in contenido:
                raise ExcepcionSistema("Servicio temporalmente no disponible (código SICOF-503)")

            # Verificar si retornó con alerta
            alerta = self.pagina.locator("[role='alert']")
            if alerta.count() > 0 and alerta.first.is_visible():
                raise ExcepcionNegocio(alerta.first.inner_text().strip())

            # Verificar causación registrada y extraer número
            match = re.search(r"CXP-\d{4}-\d{6}", contenido)
            if match:
                return match.group(0)

            raise ExcepcionSistema("No se pudo obtener el número de causación en la respuesta de confirmación")

        except (ExcepcionNegocio, ExcepcionSistema):
            raise
        except PlaywrightTimeoutError as e:
            raise ExcepcionSistema(f"Tiempo de espera agotado al confirmar causación: {e}")
        except Exception as e:
            raise ExcepcionSistema(f"Error técnico al confirmar causación: {e}")
