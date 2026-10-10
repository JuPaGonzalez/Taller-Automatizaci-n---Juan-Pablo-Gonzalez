# Guía Paso a Paso: Configuración de Microsoft 365, Flujos de Power Automate y Evidencias

**Prefijo:** `juanp.gonzalezz`  
**Umbral de Aprobación:** COP 5.000.000 (Código Impar)  
**Correo de notificación/aprobación:** `juanp.gonzalezz@upb.edu.co`  

---

## Paso 1: Configurar Listas en SharePoint y Archivos en OneDrive

### 1.1 Lista `juanp.gonzalezz-Facturas`
1. Ingresa a SharePoint con tu cuenta institucional.
2. Haz clic en **+ Nuevo** > **Lista** > **Desde Excel**.
3. Carga el archivo `src_base/datos/estructura_facturas.xlsx`.
4. Asigna como nombre de lista: `juanp.gonzalezz-Facturas`.
5. Asegúrate de los tipos de columna:
   - `Factura`: Texto de una línea
   - `NIT`: Número
   - `Proveedor`: Texto de una línea
   - `Valor`: Número
   - `CentroCosto`: Texto de una línea
   - `FechaFactura`: Fecha y hora
   - `Estado`: Texto o Elección (Valores: Pendiente, Aprobada, Rechazada, Causada, Rechazada en causación)
   - `Causacion`: Texto de una línea
   - `Observaciones`: Texto de una línea
6. Una vez creada la lista, **elimina la fila de ejemplo** (`EJEMPLO-001`).

### 1.2 Lista `juanp.gonzalezz-Bitacora`
1. En el mismo sitio de SharePoint, crea una lista en blanco llamada `juanp.gonzalezz-Bitacora`.
2. Conserva la columna predeterminada `Title` (renómbrala visiblemente a `Titulo` si lo deseas, o usa el campo Título).
3. Agrega una columna de texto llamada `Detalle` (Texto de múltiples líneas o una línea).

### 1.3 Archivos en OneDrive para la Empresa
1. Ingresa a OneDrive institucional.
2. Sube el archivo `src_base/datos/por_radicar.xlsx` y cámbiale el nombre a `juanp.gonzalezz-por_radicar.xlsx`.
   - Este libro tiene la tabla de Excel `PorRadicar`.
3. Sube `robot_causaciones/salida/resultados.xlsx` (o el que generó el robot) con el nombre `juanp.gonzalezz-resultados.xlsx`.
   - Este libro tiene la tabla de Excel `Resultados`.

---

## Paso 2: Construir el Flujo 1 (`juanp.gonzalezz-aprobacion-facturas`)

En **make.powerautomate.com**, crea un **Flujo de nube automatizado**:
- **Nombre:** `juanp.gonzalezz-aprobacion-facturas`
- **Disparador:** SharePoint - *Cuando se crea un elemento*
  - Dirección del sitio: Tu sitio de SharePoint
  - Nombre de la lista: `juanp.gonzalezz-Facturas`

### Estructura de Control de Errores (Try / Catch):
1. Agrega una acción **Ámbito** (Control - Scope) y nómbrala: `Intentar`.
2. Debajo de `Intentar`, agrega otro **Ámbito** y nómbralo: `Capturar`.
3. En el menú de tres puntos (...) de `Capturar`, selecciona **Configurar ejecución posterior** (Configure run after):
   - Marca únicamente: **ha fallado** (has failed) y **se ha agotado el tiempo de espera** (has timed out).
   - Desmarca "es correcta" y "se ha omitido".

### Dentro del ámbito `Capturar`:
- Agrega la acción **Crear elemento** (SharePoint):
  - Dirección del sitio: Tu sitio de SharePoint
  - Nombre de la lista: `juanp.gonzalezz-Bitacora`
  - `Titulo`: `triggerOutputs()?['body/Factura']`
  - `Detalle`: `concat('Error al procesar factura ', triggerOutputs()?['body/Factura'], ' en el flujo de aprobación')`

### Dentro del ámbito `Intentar`:
1. Agrega una **Condición** (Control):
   - Lado izquierdo: `int(triggerOutputs()?['body/Valor'])` (o el campo `Valor`)
   - Operador: **es mayor que**
   - Lado derecho: `5000000`

#### Rama "En caso negativo" (Valor <= 5.000.000 - Aprobación Automática):
1. **Actualizar elemento** (SharePoint):
   - Sitio y Lista: `juanp.gonzalezz-Facturas`
   - Id: `triggerOutputs()?['body/ID']`
   - `Estado`: `Aprobada`
2. **Agregar una fila a una tabla** (Excel Online - Business):
   - Ubicación: OneDrive para la Empresa
   - Biblioteca: OneDrive
   - Archivo: `juanp.gonzalezz-por_radicar.xlsx`
   - Tabla: `PorRadicar`
   - Campos:
     - `IdLista`: `triggerOutputs()?['body/ID']`
     - `Factura`: `triggerOutputs()?['body/Factura']`
     - `NIT`: `triggerOutputs()?['body/NIT']`
     - `Proveedor`: `triggerOutputs()?['body/Proveedor']`
     - `Valor`: `triggerOutputs()?['body/Valor']`
     - `CentroCosto`: `triggerOutputs()?['body/CentroCosto']`
     - `FechaFactura`: `formatDateTime(triggerOutputs()?['body/FechaFactura'], 'yyyy-MM-dd')`

#### Rama "En caso positivo" (Valor > 5.000.000 - Requiere Aprobación):
1. **Iniciar y esperar una aprobación** (Aprobaciones):
   - Tipo de aprobación: `Aprobar/rechazar - Todos deben aprobar`
   - Título: `Aprobación de factura @{triggerOutputs()?['body/Factura']} - COP @{triggerOutputs()?['body/Valor']}`
   - Asignado a: `juanp.gonzalezz@upb.edu.co`
   - Detalles: `Por favor revisar la factura @{triggerOutputs()?['body/Factura']} del proveedor @{triggerOutputs()?['body/Proveedor']} por valor de @{triggerOutputs()?['body/Valor']}.`
2. Agrega una **Condición**:
   - Lado izquierdo: `Resultado` (de la acción de aprobación, `body('Iniciar_y_esperar_una_aprobación')?['responseSummary']` o `responses[0]['responder']...` / campo `Outcome`)
   - Operador: **es igual a**
   - Lado derecho: `Approve`
   - **Rama Sí (Aprobada por el jefe):**
     - **Actualizar elemento** (SharePoint):
       - Id: `triggerOutputs()?['body/ID']`
       - `Estado`: `Aprobada`
     - **Agregar una fila a una tabla** (Excel Online):
       - Exactamente los mismos campos mapeados a `PorRadicar` que en la rama automática.
   - **Rama No (Rechazada por el jefe):**
     - **Actualizar elemento** (SharePoint):
       - Id: `triggerOutputs()?['body/ID']`
       - `Estado`: `Rechazada`
     - *(NO agregar fila a Excel)*

---

## Paso 3: Construir el Flujo 2 (`juanp.gonzalezz-cierre-radicacion`)

En **make.powerautomate.com**, crea un **Flujo de nube instantáneo**:
- **Nombre:** `juanp.gonzalezz-cierre-radicacion`
- **Disparador:** *Activar un flujo manualmente*

### Acciones del flujo:
1. **Enumerar las filas presentes en una tabla** (Excel Online - Business):
   - Ubicación: OneDrive para la Empresa
   - Biblioteca: OneDrive
   - Archivo: `juanp.gonzalezz-resultados.xlsx`
   - Tabla: `Resultados`

2. **Aplicar a cada uno** (Control):
   - Seleccionar una salida: `value` (de Enumerar las filas presentes en una tabla)
   - Dentro del bucle:
     1. **Obtener elemento** (SharePoint):
        - Lista: `juanp.gonzalezz-Facturas`
        - Id: `int(items('Aplicar_a_cada_uno')?['IdLista'])`
     2. **Condición**:
        - Lado izquierdo: `body('Obtener_elemento')?['Estado']` (o campo Estado)
        - Operador: **es igual a**
        - Lado derecho: `Aprobada`
        - **Rama Sí:**
          - Agrega una **Condición** o **Modificador (Switch)** evaluando `items('Aplicar_a_cada_uno')?['Estado']`:
            - **Si es igual a `CAUSADA` o `YA_CAUSADA`:**
              - **Actualizar elemento** (SharePoint):
                - Id: `items('Aplicar_a_cada_uno')?['IdLista']`
                - `Estado`: `Causada`
                - `Causacion`: `items('Aplicar_a_cada_uno')?['Causacion']`
            - **Si es igual a `RECHAZADA`:**
              - **Actualizar elemento** (SharePoint):
                - Id: `items('Aplicar_a_cada_uno')?['IdLista']`
                - `Estado`: `Rechazada en causación`
                - `Observaciones`: `items('Aplicar_a_cada_uno')?['Detalle']`
            - **Si es igual a `FALLA_SISTEMA`:**
              - Dejar vacío (no se actualiza, permanece en Aprobada).
        - **Rama No:**
          - Dejar vacío (garantiza idempotencia si ya fue procesada).

3. Fuera del bucle `Aplicar a cada uno`:
   1. **Crear tabla HTML** (Operación de datos):
      - Desde: `body('Enumerar_las_filas_presentes_en_una_tabla')?['value']`
      - Columnas: Personalizado
        - `Factura` -> `item()?['Factura']`
        - `NIT` -> `item()?['NIT']`
        - `Estado` -> `item()?['Estado']`
        - `Causacion` -> `item()?['Causacion']`
        - `Detalle` -> `item()?['Detalle']`
   2. **Enviar correo electrónico (V2)** (Office 365 Outlook):
      - Para: `juanp.gonzalezz@upb.edu.co`
      - Asunto: `Resumen de Radicación de Facturas SICOF`
      - Cuerpo:
        ```html
        <p>Cordial saludo,</p>
        <p>A continuación se presenta el resumen del ciclo de radicación de facturas:</p>
        @{body('Crear_tabla_HTML')}
        <p>Atentamente,<br>Sistema Automatizado de Cuentas por Pagar</p>
        ```

---

## Paso 4: Ejecución de las 7 Facturas de Prueba

Con el flujo `juanp.gonzalezz-aprobacion-facturas` activado:
1. Crea en la lista `juanp.gonzalezz-Facturas` las 7 facturas de `facturas_prueba.xlsx` con estado `Pendiente`:
   - **Factura 1 (FE-20871, $1.850.000):** Se aprueba automáticamente.
   - **Factura 2 (TR-5530, $6.400.000):** Te llega correo/notificación de Teams de Aprobación. Haz clic en **Aprobar**.
   - **Factura 3 (IQ-0912, $7.900.000):** Te llega aprobación. Haz clic en **Rechazar**.
   - **Factura 4 (ST-3307, $4.200.000):** Como tu umbral es $5.000.000 (impar), se aprueba automáticamente.
   - **Factura 5 (MI-0077, $950.000):** Se aprueba automáticamente.
   - **Factura 6 (PS-1188, $620.000):** Se aprueba automáticamente.
   - **Factura 7 (FE-20871, $2.300.000):** Se aprueba automáticamente.

2. Descarga `juanp.gonzalezz-por_radicar.xlsx` a `robot_causaciones/datos/por_radicar.xlsx`.
3. Ejecuta el robot:
   ```bash
   cd robot_causaciones
   uv run python main.py
   ```
4. Sube `robot_causaciones/salida/resultados.xlsx` a OneDrive reemplazando `juanp.gonzalezz-resultados.xlsx`.
5. Ejecuta manualmente el flujo `juanp.gonzalezz-cierre-radicacion`.

---

## Paso 5: Captura de Evidencias Requeridas

Guarda en la carpeta `evidencias/` los siguientes archivos:
1. **`evidencias/lista_final.png`**: Captura de pantalla de la lista `juanp.gonzalezz-Facturas` donde se vean las 7 facturas en su estado final:
   - 1: Causada (CXP-2026-000001)
   - 2: Causada (CXP-2026-000002)
   - 3: Rechazada
   - 4: Causada (CXP-2026-000003)
   - 5: Rechazada en causación (Observación: El NIT 900999001 no está registrado...)
   - 6: Rechazada en causación (Observación: La fecha de factura no puede ser posterior...)
   - 7: Causada (CXP-2026-000004)
2. **`evidencias/historial_aprobacion.png`**: Captura de la pantalla del historial de ejecuciones de `juanp.gonzalezz-aprobacion-facturas` mostrando las ejecuciones de las facturas de prueba con estado correcto.
3. **`evidencias/fallo_capturado.png`**: Provoca un fallo (por ejemplo renombrando temporalmente el archivo de OneDrive antes de crear una factura de prueba o pasando un valor que falle en Excel). Captura la pantalla mostrando el ámbito `Intentar` fallido (cruz roja), `Capturar` ejecutado (check verde) y al lado la lista `juanp.gonzalezz-Bitacora` con el registro del error.
4. **`evidencias/cierre.png`**: Captura de pantalla de la ejecución exitosa del flujo `juanp.gonzalezz-cierre-radicacion` y la ventana del correo recibido en Outlook con la tabla HTML de resultados.

---

## Paso 6: Exportar los Flujos (.zip)

1. En **make.powerautomate.com**, entra a `juanp.gonzalezz-aprobacion-facturas`.
2. Haz clic en **Exportar** > **Paquete (.zip)**.
3. Guárdalo como: `flujos/juanp.gonzalezz-aprobacion-facturas.zip`.
4. Repite el proceso para `juanp.gonzalezz-cierre-radicacion` y guárdalo como: `flujos/juanp.gonzalezz-cierre-radicacion.zip`.

---

## Paso 7: Publicación en GitHub y Envío del Correo

1. En la carpeta del proyecto, sube los cambios a tu repositorio público de GitHub:
   ```bash
   git add .
   git commit -m "Entrega taller de automatizacion - robot y evidencias"
   git push origin main
   ```
2. Redacta el correo a: `juan.canoc@upb.edu.co`
   - **Asunto:** `[Plataformas] Taller Automatización - Juan Pablo González`
   - **Cuerpo:**
     ```text
     Profesor Juan Cano,

     Envío la entrega del Taller de Automatización: Radicación automatizada de facturas de proveedores.

     Nombre: Juan Pablo González
     Código: (Tu código estudiantil)
     Repositorio GitHub: https://github.com/tu-usuario/taller-automatizacion-juanp.gonzalezz

     Quedo atento.
     ```
