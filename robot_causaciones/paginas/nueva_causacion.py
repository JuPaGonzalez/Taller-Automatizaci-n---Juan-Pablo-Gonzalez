from datetime import date
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from paginas.base import PaginaBase
from excepciones import ExcepcionNegocio, ExcepcionSistema


class PaginaNuevaCausacion(PaginaBase):
    def llenar_y_continuar(
        self,
        nit: int,
        factura: str,
        fecha_factura: date,
        valor: int,
        centro_costo: str,
    ) -> None:
        """
        Navega a /causaciones/nueva, espera a que se habilite el formulario (retardo maestro),
        valida el centro de costo, diligencia los campos y pulsa Continuar.
        Lanza ExcepcionNegocio si el portal devuelve mensaje con role='alert' o centro inválido.
        """
        url_nueva = f"{self.url_base}/causaciones/nueva"
        try:
            self.pagina.goto(url_nueva, wait_until="domcontentloaded")

            # Esperar a que termine la carga asíncrona (1200ms) y el botón se habilite
            btn_continuar = self.pagina.get_by_role("button", name="Continuar")
            btn_continuar.wait_for(state="visible", timeout=15000)
            self.pagina.wait_for_function(
                "() => { const b = document.querySelector('button[type=\"submit\"]'); return b && !b.disabled; }",
                timeout=15000,
            )

            # Validación de Centro de Costo en la lista desplegable
            opciones_centro = self.pagina.eval_on_selector(
                "select[name='centro']",
                "el => Array.from(el.options).map(o => o.value).filter(v => v !== '')",
            )
            if centro_costo not in opciones_centro:
                raise ExcepcionNegocio("Seleccione un centro de costo válido")

            # Diligenciar campos utilizando selectores basados en etiquetas visibles
            # (compatibles tanto con UI v1 como con UI v2)
            self.pagina.get_by_label("NIT del proveedor").fill(str(nit))
            self.pagina.get_by_label("Número de factura").fill(factura)
            self.pagina.get_by_label("Fecha de factura").fill(fecha_factura.strftime("%d/%m/%Y"))
            self.pagina.get_by_label("Valor total").fill(str(valor))
            self.pagina.get_by_label("Centro de costo").select_option(value=centro_costo)

            # Pulsar Continuar
            btn_continuar.click()

            # Verificar si SICOF rechazó con un mensaje en role='alert'
            # (ej. NIT no registrado, fecha posterior, etc.)
            alerta = self.pagina.locator("[role='alert']")
            try:
                if alerta.is_visible(timeout=3000):
                    mensaje_alerta = alerta.inner_text().strip()
                    raise ExcepcionNegocio(mensaje_alerta)
            except ExcepcionNegocio:
                raise
            except Exception:
                pass

            # Si no hay alerta, verificar que hayamos llegado a la pantalla de confirmación
            self.pagina.wait_for_url("**/causaciones/revision**", timeout=10000)

        except ExcepcionNegocio:
            raise
        except PlaywrightTimeoutError as e:
            raise ExcepcionSistema(f"Tiempo de espera agotado en formulario de causación: {e}")
        except Exception as e:
            raise ExcepcionSistema(f"Error técnico en formulario de causación: {e}")
