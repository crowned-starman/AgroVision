# AgroVision 🌾

Plataforma geoespacial de compatibilidad agrícola. Analiza terrenos usando
imágenes satelitales (Sentinel-2 vía Google Earth Engine) y calcula qué
cultivos son compatibles con las condiciones del terreno.

> **Modo actual:** datos simulados — sin dependencia de GEE.

---

## Requisitos previos

| Herramienta | Versión mínima | Verificar con |
|---|---|---|
| Docker Desktop | 4.x | `docker --version` |
| Node.js | 18.x | `node --version` |
| Python | 3.10+ | `python --version` |

### Instalar Node.js (si no lo tienes)
1. Ir a https://nodejs.org
2. Descargar la versión **LTS** (la recomendada)
3. Instalar con las opciones por defecto
4. Abrir una terminal nueva y verificar: `node --version`

---

## Setup inicial (solo la primera vez)

### 1. Abrir terminal en la carpeta del proyecto

```
Clic derecho en la carpeta agrovision → "Abrir en Terminal"
```

### 2. Levantar la base de datos

```bash
docker compose up -d db
```

Espera que el contenedor esté healthy (unos 10 segundos):

```bash
docker compose ps
```

El estado debe decir `healthy`.

### 3. Levantar el backend

```bash
docker compose up -d backend
```

Verificar que está corriendo:

```bash
curl http://localhost:8000/api/v1/health
```

Debe responder: `{"status":"ok","version":"1.0.0","mode":"mock"}`

### 4. Instalar dependencias del frontend

```bash
cd frontend
npm install
cd ..
```

---

## Ejecutar el proyecto

### Cada vez que quieras usarlo:

**Terminal 1 — backend + base de datos:**
```bash
docker compose up
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

Abrir el navegador en: **http://localhost:5173**

---

## Cómo usar AgroVision

1. **Dibujar el terreno:** En el mapa, usa el ícono de polígono (barra izquierda) y dibuja el contorno del terreno que quieres analizar. Haz clic para cada vértice; doble clic para cerrar.

2. **Analizar:** Presiona el botón "Analizar terreno" que aparece debajo del mapa.

3. **Ver resultados:** El panel derecho muestra:
   - Variables ambientales del terreno (NDVI, temperatura, precipitación, suelo)
   - Lista de cultivos ordenados por score de compatibilidad
   - Detalle por dimensión y factores limitantes al hacer clic en cada cultivo

4. **Filtrar cultivos:** Usa las pestañas (Alto / Medio / Bajo / Incompatible) para filtrar los resultados.

---

## Estructura del proyecto

```
agrovision/
├── backend/                  # FastAPI
│   ├── modules/
│   │   ├── gee/mock_client.py     ← aquí se conecta GEE real después
│   │   ├── geo/feature_extractor.py
│   │   └── scoring/engine.py
│   └── data/agronomy/crops.yaml   ← base de cultivos (editable)
├── frontend/                 # React + Leaflet
└── docker-compose.yml
```

---

## Agregar o modificar cultivos

Edita `backend/data/agronomy/crops.yaml`. El backend recarga el archivo
en cada reinicio. Formato de ejemplo:

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

## Conectar Google Earth Engine (si se tiene acceso)

1. Solicitar acceso en https://earthengine.google.com
2. Crear un archivo `backend/.env`:
   ```
   DATA_MODE=gee
   GEE_PROJECT=tu-proyecto-gee
   ```
3. Implementar `backend/modules/gee/client.py` con la misma firma que `mock_client.py`:
   ```python
   def get_environmental_data(polygon_geojson: dict) -> dict:
       ...  # llamadas reales a GEE
   ```
4. Reiniciar el backend: `docker compose restart backend`

El resto del sistema no cambia.

---

## Comandos útiles

```bash
# Ver logs del backend
docker compose logs backend -f

# Reiniciar solo el backend (tras cambios en Python)
docker compose restart backend

# Detener todo
docker compose down

# Borrar base de datos y empezar desde cero
docker compose down -v

# Abrir psql para inspeccionar la DB
docker exec -it agrovision_db psql -U agrovision -d agrovision
```

---

## Problemas comunes

**El backend no conecta con la DB:**
```bash
docker compose ps   # verificar que db esté "healthy"
docker compose restart backend
```

**`npm install` falla:**
Asegúrate de tener Node.js 18+ y ejecutar el comando dentro de la carpeta `frontend/`.

**El mapa no carga:**
Revisa que el frontend esté corriendo en puerto 5173 (`npm run dev`) y el backend en 8000.

**Error "polígono inválido":**
Dibuja el polígono de forma que no se crucen los lados. Usa puntos separados para cada vértice.
