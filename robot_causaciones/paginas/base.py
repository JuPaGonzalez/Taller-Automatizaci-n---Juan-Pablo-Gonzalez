from playwright.sync_api import Page


class PaginaBase:
    def __init__(self, pagina: Page, url_base: str) -> None:
        self.pagina = pagina
        self.url_base = url_base.rstrip("/")
