# Taller de Automatización: Radicación Automatizada de Facturas de Proveedores

**Estudiante:** Juan Pablo González  
**Correo institucional:** juanp.gonzalezz@upb.edu.co  
**Prefijo institucional:** `juanp.gonzalezz`  
**Código estudiantil:** Impar (Umbral de aprobación: **COP 5.000.000**)  
**Materia:** Plataformas de Desarrollo de Software - UPB 2026-2  

---

## 1. Estructura del Repositorio

```text
.
├── robot_causaciones/
│   ├── datos/
│   │   └── por_radicar.xlsx         # Cola de trabajo descargada de OneDrive (tabla PorRadicar)
│   ├── paginas/                     # Page Object Model (POM) compatible con UI v1 y UI v2
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── login.py
│   │   ├── consulta.py              # Idempotencia previa en SICOF
│   │   ├── nueva_causacion.py       # Diligenciamiento y validación de alertas
│   │   └── revision.py              # Confirmación y captura de fallas 503
│   ├── salida/                      # Salida local de la ejecución (ignorado en git)
│   │   ├── bot.log
│   │   ├── resultados.xlsx
│   │   └── evidencias/
│   ├── config.py                    # Carga de variables de entorno y rutas
│   ├── excepciones.py               # ExcepcionNegocio y ExcepcionSistema
│   ├── gestor_excel.py              # Lectura y escritura conforme al contrato estricto
│   ├── modelo.py                    # Dataclasses FacturaEntrada y ResultadoFactura
│   ├── robot.py                     # Orquestador del lote y reintentos técnicos
│   ├── main.py                      # Punto de entrada principal
│   ├── pyproject.toml               # Dependencias fijadas según especificación
│   ├── uv.lock                      # Lockfile generado con uv
│   ├── .env.example                 # Plantilla de configuración
│   └── .gitignore
├── flujos/
│   ├── juanp.gonzalezz-aprobacion-facturas.zip   # Flujo de aprobación empaquetado
│   └── juanp.gonzalezz-cierre-radicacion.zip     # Flujo de cierre empaquetado
├── evidencias/
│   ├── bot.log                      # Log generado tras procesar las 6 facturas
│   ├── resultados.xlsx              # Excel con tabla Resultados según contrato
│   ├── lista_final.png              # Estado final de la lista juanp.gonzalezz-Facturas
│   ├── historial_aprobacion.png     # Historial de ejecuciones del flujo de aprobación
│   ├── fallo_capturado.png          # Ejecución con Intentar fallido y Capturar ejecutado en Bitacora
│   └── cierre.png                   # Ejecución del flujo de cierre y correo con tabla HTML
├── src_base/                        # Portal SICOF y datos base entregados
├── .gitignore
└── README.md
```

---

## 2. Requisitos y Ejecución del Robot RPA

El robot está construido en **Python 3.13** y utiliza **uv** (0.8+) para la gestión de dependencias y ejecución:

### Dependencias fijadas (`pyproject.toml`):
- `playwright==1.62.0`
- `openpyxl==3.1.5`
- `python-dotenv==1.2.3`
- `tenacity==9.1.4`

### Configuración de entorno (`robot_causaciones/.env`):
Crear o verificar el archivo `robot_causaciones/.env` (basado en `.env.example`):
```env
PORTAL_URL=http://127.0.0.1:8020
PORTAL_USUARIO=operador.rpa
PORTAL_CLAVE=CxpSicof2026
BOT_HEADLESS=true
```

### Ejecución del Robot:
1. Iniciar el portal SICOF (desde `src_base/portal_sicof/`):
   ```bash
   uv run python -m portal --inestable
   ```
2. Ejecutar el robot (desde la carpeta `robot_causaciones/`):
   ```bash
   cd robot_causaciones
   uv run python main.py
   ```

---

## 3. Características Técnicas del Robot

1. **Robustez y Resiliencia UI (v1 y v2):**
   - Utiliza selectores accesibles (`get_by_label`, `get_by_role`, `get_by_text`) que garantizan funcionamiento transparente tanto con la interfaz estándar (v1) como con la interfaz rediseñada (`--ui v2`).
   - Maneja el retardo asíncrono de carga del maestro de proveedores (1200 ms) esperando a que los controles y el botón de envío se encuentren interactivos y habilitados.

2. **Idempotencia:**
   - Antes de radicar, consulta `/causaciones?factura=<número>`.
   - Si ya existe una causación previa con el mismo NIT y factura, no duplica el registro y marca el estado como `YA_CAUSADA` con el número existente.
   - Trata como facturas independientes aquellas que comparten número pero tienen diferente NIT (ej. Factura 1 y Factura 7).

3. **Manejo de Excepciones y Reintentos:**
   - **Excepciones de Negocio (`ExcepcionNegocio`):**
     - Alertas de SICOF (`role="alert"`), como proveedor no registrado o fecha inválida.
     - Centros de costo inexistentes en la lista desplegable.
     - Facturas con fecha posterior al día de ejecución o valor menor o igual a cero.
     - Se registran como `RECHAZADA` en la tabla de resultados y en el log, sin reintentos.
   - **Excepciones de Sistema (`ExcepcionSistema`):**
     - Pantalla de *Servicio temporalmente no disponible* (código `SICOF-503`), errores de conexión o tiempos de espera agotados.
     - Se reintentan hasta un máximo de 3 veces por factura.
     - Cada reintento se documenta en `salida/bot.log`.
     - Si se agotan los 3 intentos, se toma captura de pantalla en `salida/evidencias/` y se marca como `FALLA_SISTEMA`.
   - **No interrupción del lote:** Ningún error individual detiene el procesamiento de las demás facturas.

4. **Contrato de Salida (`salida/resultados.xlsx`):**
   - Tabla de Excel llamada `Resultados` con las columnas exactas:
     - `IdLista`: Entero.
     - `Factura`: Texto.
     - `NIT`: Entero sin separadores.
     - `Estado`: `CAUSADA`, `YA_CAUSADA`, `RECHAZADA` o `FALLA_SISTEMA`.
     - `Causacion`: `CXP-AAAA-NNNNNN` si aplica, vacío en caso contrario.
     - `Detalle`: Motivo del rechazo o error, vacío si quedó causada.

---

## 4. Flujos de Power Automate Cloud

### Flujo 1: `juanp.gonzalezz-aprobacion-facturas`
- **Disparador:** *Cuando se crea un elemento* sobre la lista SharePoint `juanp.gonzalezz-Facturas`.
- **Estructura Try-Catch:**
  - **Ámbito `Intentar`:** Contiene toda la lógica de aprobación y registro.
  - **Ámbito `Capturar`:** Configurado con ejecución posterior para ejecutarse solo si `Intentar` falla (`hasFailed`). Crea un elemento en la lista `juanp.gonzalezz-Bitacora` con el número de factura en `Titulo` y el detalle del error en `Detalle`.
- **Regla de Aprobación:**
  - Umbral: **COP 5.000.000** (código impar).
  - Si `Valor <= 5.000.000`: Pone `Estado` en **Aprobada** y agrega la fila a la tabla `PorRadicar` en OneDrive (`juanp.gonzalezz-por_radicar.xlsx`).
  - Si `Valor > 5.000.000`: Solicita aprobación (*Aprobar/rechazar - Todos deben aprobar*) asignada al usuario. Si se aprueba, pasa a **Aprobada** y se añade a `PorRadicar`. Si se rechaza, pasa a **Rechazada** y **no** se añade a `PorRadicar`.

### Flujo 2: `juanp.gonzalezz-cierre-radicacion`
- **Disparador:** *Activar un flujo manualmente*.
- **Acciones:**
  - Lee la tabla `Resultados` desde `juanp.gonzalezz-resultados.xlsx` en OneDrive.
  - Itera sobre cada fila y consulta el elemento correspondiente en `juanp.gonzalezz-Facturas` mediante `IdLista`.
  - Si el estado en SharePoint es **Aprobada**:
    - `CAUSADA` o `YA_CAUSADA`: Actualiza a `Causada` y registra `Causacion`.
    - `RECHAZADA`: Actualiza a `Rechazada en causación` y registra el motivo en `Observaciones`.
    - `FALLA_SISTEMA`: No se modifica (queda en `Aprobada` para el siguiente ciclo).
  - Si el estado ya no es `Aprobada`, no se modifica (garantiza idempotencia).
  - Genera una tabla HTML con las columnas `Factura`, `NIT`, `Estado`, `Causacion`, `Detalle`.
  - Envía un correo con el resumen a la cuenta propia (`juanp.gonzalezz@upb.edu.co`).
# Taller-Automatizaci-n---Juan-Pablo-Gonzalez
