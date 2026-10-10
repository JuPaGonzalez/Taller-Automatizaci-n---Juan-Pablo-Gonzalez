from urllib.parse import quote
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from paginas.base import PaginaBase
from excepciones import ExcepcionSistema


class PaginaConsulta(PaginaBase):
    def buscar_causacion_existente(self, nit: int, factura: str) -> str | None:
        """
        Consulta en SICOF (/causaciones?factura=...) si ya existe una causación
        con la pareja exacta (NIT, factura).
        Retorna el número de causación (CXP-AAAA-NNNNNN) si existe, o None si no.
        """
        url_consulta = f"{self.url_base}/causaciones?factura={quote(factura)}"
        try:
            self.pagina.goto(url_consulta, wait_until="domcontentloaded")
            filas = self.pagina.locator("table tbody tr")
            conteo = filas.count()

            for i in range(conteo):
                fila = filas.nth(i)
                celdas = fila.locator("td")
                if celdas.count() < 4:
                    # Fila tipo "No hay causaciones registradas"
                    continue

                numero_cxp = celdas.nth(0).inner_text().strip()
                nit_celda = celdas.nth(1).inner_text().strip()
                factura_celda = celdas.nth(3).inner_text().strip()

                if nit_celda == str(nit) and factura_celda.upper() == factura.strip().upper():
                    return numero_cxp

            return None
        except PlaywrightTimeoutError as e:
            raise ExcepcionSistema(f"Tiempo de espera agotado al consultar causaciones: {e}")
        except Exception as e:
            raise ExcepcionSistema(f"Error al consultar causaciones en SICOF: {e}")
