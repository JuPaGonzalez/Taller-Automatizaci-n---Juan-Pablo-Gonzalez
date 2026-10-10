from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from paginas.base import PaginaBase
from excepciones import ExcepcionSistema


class PaginaLogin(PaginaBase):
    def iniciar_sesion(self, usuario: str, clave: str) -> None:
        """Inicia sesión en SICOF si no está autenticado."""
        url_login = f"{self.url_base}/login"
        try:
            self.pagina.goto(url_login, wait_until="domcontentloaded")
            # Si ya está autenticado, el portal redirige a /causaciones/nueva
            if "/causaciones" in self.pagina.url:
                return

            self.pagina.get_by_label("Usuario").fill(usuario)
            self.pagina.get_by_label("Contraseña").fill(clave)
            self.pagina.get_by_role("button", name="Ingresar").click()
            self.pagina.wait_for_url("**/causaciones/**", timeout=10000)
        except PlaywrightTimeoutError as e:
            raise ExcepcionSistema(f"Tiempo de espera agotado al iniciar sesión: {e}")
        except Exception as e:
            raise ExcepcionSistema(f"Error de conexión o sistema al iniciar sesión: {e}")
