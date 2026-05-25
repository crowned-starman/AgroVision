# AgroVision 🌾

Plataforma geoespacial de compatibilidad agrícola. Analiza terrenos usando variables ambientales e imágenes satelitales para calcular qué cultivos son compatibles con las condiciones del terreno.

## Modos de operación

| Modo | Descripción |
|---|---|
| `mock` | Datos simulados — sin dependencias externas, ideal para desarrollo |
| `gee` | Datos reales desde Sentinel-2 vía Google Earth Engine |

---

## Requisitos previos

| Herramienta | Versión mínima | Verificar con |
|---|---|---|
| Docker Desktop | 4.x | `docker --version` |
| Node.js | 18.x | `node --version` |

### Instalar Node.js
1. Ir a https://nodejs.org y descargar la versión **LTS**
2. Instalar con opciones por defecto
3. Abrir una terminal **nueva** y verificar: `node --version`

### Nota para usuarios de Windows
Si `npm` da error de permisos en PowerShell, ejecuta esto como administrador una sola vez:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## Setup inicial (solo la primera vez)

### 1. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto. Puedes copiar `.env.example` como base:

```bash
copy .env.example .env
```

Luego edita `.env` y rellena los valores:

```
POSTGRES_PASSWORD=elige_una_password_segura
DATABASE_URL=postgresql://agrovision:elige_una_password_segura@db:5432/agrovision
GEE_PROJECT=tu-project-id-de-gee
DATA_MODE=mock
GEE_CREDENTIALS_JSON=
GEE_REFRESH_TOKEN=
```

> ⚠️ Nunca subas el archivo `.env` a GitHub — ya está en `.gitignore`.
> La contraseña de PostgreSQL es solo local; elige cualquier valor seguro.

### 2. Levantar backend y base de datos

```bash
docker compose up --build
```

### 3. Instalar dependencias del frontend

Abre una segunda terminal:

```bash
cd frontend
npm install
```

---

## Ejecutar el proyecto

**Terminal 1 — backend:**
```bash
docker compose up
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

Abrir en el navegador: **http://localhost:5173**

---

## Cómo usar AgroVision

1. **Dibujar terreno** — usa el ícono de polígono en la barra izquierda del mapa. Clic en cada vértice, doble clic para cerrar.
2. **Analizar** — presiona el botón "Analizar terreno".
3. **Ver resultados** — el panel derecho muestra variables ambientales y scores de compatibilidad por cultivo.
4. **Filtrar** — usa las pestañas Alto / Medio / Bajo / Incompatible.
5. **Ver detalle** — haz clic en cualquier cultivo para ver el desglose por dimensión y factores limitantes.

---

## Conectar Google Earth Engine

1. Solicitar acceso académico en https://earthengine.google.com/signup
2. Una vez aprobado, autenticarte localmente:
   ```bash
   pip install earthengine-api
   earthengine authenticate
   ```
3. Abre el archivo de credenciales generado:
   ```
   C:\Users\TU_USUARIO\.config\earthengine\credentials
   ```
4. Copia **todo el contenido** del archivo (es un JSON en una sola línea) y pégalo en `.env`:
   ```
   DATA_MODE=gee
   GEE_PROJECT=tu-project-id
   GEE_CREDENTIALS_JSON={"redirect_uri": "http://localhost:8085", "refresh_token": "..."}
   ```
5. Reiniciar:
   ```bash
   docker compose down
   docker compose up --build
   ```

---

## Agregar cultivos

Edita `backend/data/agronomy/crops.yaml`. El backend recarga el archivo automáticamente al detectar cambios. Ejemplo mínimo:

```yaml
- id: mi_cultivo
  name: Nombre del cultivo
  scientific_name: Genus species
  category: cereal
  active: true
  description: Descripción breve
  requirements:
    temperature:
      min_c: 10
      optimal_min_c: 18
      optimal_max_c: 28
      max_c: 36
      weight: 0.25
    precipitation:
      annual_min_mm: 500
      annual_optimal_mm: 800
      annual_max_mm: 1400
      weight: 0.20
    soil_ph:
      min: 5.5
      optimal_min: 6.0
      optimal_max: 7.0
      max: 8.0
      weight: 0.20
    ndvi_baseline:
      min_viable: 0.12
      weight: 0.15
    slope:
      max_degrees: 12
      weight: 0.10
    soil_texture:
      preferred: ["loam", "clay_loam"]
      weight: 0.10
  limiting_factors:
    - name: helada
      condition: temp_min_c < 2
      severity: critical
      message: Este cultivo no tolera heladas
```

---

## Estructura del proyecto

```
agrovision/
├── backend/
│   ├── main.py                          # FastAPI entry point
│   ├── config.py                        # Variables de entorno
│   ├── database.py                      # PostgreSQL + PostGIS
│   ├── api/routes/
│   │   ├── analysis.py                  # POST /analyze
│   │   ├── crops.py                     # GET /crops
│   │   └── terrain.py                   # GET /terrain
│   ├── modules/
│   │   ├── gee/
│   │   │   ├── mock_client.py           # Datos simulados
│   │   │   └── client.py               # Cliente GEE real
│   │   ├── geo/feature_extractor.py    # Pipeline de features
│   │   └── scoring/
│   │       ├── engine.py               # Orquestador de scoring
│   │       └── rule_scorer.py          # Scoring por reglas
│   └── data/agronomy/crops.yaml        # Base agronómica (editable)
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Map/TerrainMap.jsx      # Mapa + herramientas de dibujo
│       │   └── Results/                # Panel de resultados
│       └── services/api.js             # Llamadas al backend
├── docker-compose.yml
├── .env.example                        # Plantilla de variables de entorno
└── .gitignore
```

---

## Comandos útiles

```bash
# Ver logs del backend en tiempo real
docker compose logs backend -f

# Reiniciar solo el backend
docker compose restart backend

# Detener todo
docker compose down

# Borrar base de datos y empezar desde cero
docker compose down -v

# Reconstruir imagen del backend (tras cambios en requirements.txt)
docker compose up --build
```

---

## Problemas comunes

**Variables de entorno no detectadas:**
Verificar que el archivo `.env` existe en la raíz del proyecto y tiene los valores correctos.

**Error al arrancar el backend:**
```bash
docker compose down -v
docker compose up --build
```

**`npm install` falla:**
Ejecutar desde dentro de la carpeta `frontend/`, con Node.js 18+. En Windows, ver nota sobre `Set-ExecutionPolicy` arriba.

**El mapa no carga:**
Verificar que el frontend corre en puerto 5173 y el backend en 8000.

**Error 500 al analizar:**
Revisar logs: `docker compose logs backend --tail=30`

**Polígono inválido:**
Dibujar sin que los lados se crucen. Usar al menos 3 vértices distintos.
