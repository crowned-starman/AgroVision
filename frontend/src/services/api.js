import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60_000,  // GEE puede tardar; mock es instantáneo
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Analiza un polígono GeoJSON y retorna scores de cultivos.
 * @param {object} polygonGeojson - GeoJSON geometry (type: Polygon)
 * @param {string} [name]         - Nombre opcional del terreno
 */
export async function analyzePolygon(polygonGeojson, name = null) {
  try {
    const response = await api.post('/analysis/analyze', {
      geojson: polygonGeojson,
      name,
    })
    return response.data
  } catch (err) {
    const msg = err.response?.data?.detail ?? err.message ?? 'Error desconocido'
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
}

/**
 * Retorna la lista de cultivos disponibles.
 */
export async function getCrops() {
  const response = await api.get('/crops/')
  return response.data
}

/**
 * Retorna un análisis por ID.
 */
export async function getAnalysis(analysisId) {
  const response = await api.get(`/analysis/${analysisId}`)
  return response.data
}

/**
 * Retorna los terrenos guardados.
 */
export async function getTerrains() {
  const response = await api.get('/terrain/')
  return response.data
}

export default api
