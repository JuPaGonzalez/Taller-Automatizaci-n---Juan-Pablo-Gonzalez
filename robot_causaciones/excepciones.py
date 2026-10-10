class ExcepcionNegocio(Exception):
    """Excepción de negocio: validaciones previas o rechazos del portal que no deben reintentarse."""
    pass


class ExcepcionSistema(Exception):
    """Excepción de sistema: fallas técnicas como SICOF-503, tiempos de espera o errores de conexión."""
    pass
