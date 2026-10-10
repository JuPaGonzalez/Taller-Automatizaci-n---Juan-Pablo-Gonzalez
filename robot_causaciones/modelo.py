from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class FacturaEntrada:
    id_lista: int
    factura: str
    nit: int
    proveedor: str
    valor: int
    centro_costo: str
    fecha_factura: date


@dataclass
class ResultadoFactura:
    id_lista: int
    factura: str
    nit: int
    estado: str  # CAUSADA, YA_CAUSADA, RECHAZADA, FALLA_SISTEMA
    causacion: str = ""
    detalle: str = ""
