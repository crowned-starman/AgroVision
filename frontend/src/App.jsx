import { useState } from 'react'
import TerrainMap from './components/Map/TerrainMap.jsx'
import ResultsPanel from './components/Results/ResultsPanel.jsx'
import Header from './components/UI/Header.jsx'
import { analyzePolygon } from './services/api.js'
import './App.css'

export default function App() {
  const [drawnPolygon, setDrawnPolygon] = useState(null)
  const [analysis, setAnalysis]         = useState(null)
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState(null)

  const handlePolygonDrawn = (geojson) => {
    setDrawnPolygon(geojson)
    setAnalysis(null)
    setError(null)
  }

  const handleAnalyze = async () => {
    if (!drawnPolygon) return
    setLoading(true)
    setError(null)
    try {
      const result = await analyzePolygon(drawnPolygon)
      setAnalysis(result)
    } catch (e) {
      setError(e.message || 'Error al analizar el terreno')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setDrawnPolygon(null)
    setAnalysis(null)
    setError(null)
  }

  return (
    <div className="app-shell">
      <Header />
      <div className="app-body">
        <div className="map-column">
          <TerrainMap
            onPolygonDrawn={handlePolygonDrawn}
            drawnPolygon={drawnPolygon}
          />
          <div className="map-toolbar">
            {drawnPolygon && !loading && (
              <>
                <button className="btn-primary" onClick={handleAnalyze}>
                  Analizar terreno
                </button>
                <button className="btn-ghost" onClick={handleClear}>
                  Limpiar
                </button>
              </>
            )}
            {loading && (
              <div className="analyzing-badge">
                <span className="spinner" /> Analizando…
              </div>
            )}
            {!drawnPolygon && !loading && (
              <p className="hint">
                Dibuja un polígono sobre el terreno que quieres analizar
              </p>
            )}
          </div>
          {error && <div className="error-banner">{error}</div>}
        </div>

        <div className={`results-column ${analysis ? 'has-results' : ''}`}>
          {analysis
            ? <ResultsPanel analysis={analysis} />
            : (
              <div className="results-empty">
                <div className="results-empty-icon">🌱</div>
                <p>Los resultados de compatibilidad aparecerán aquí</p>
                <small>Selecciona un terreno en el mapa y presiona "Analizar"</small>
              </div>
            )
          }
        </div>
      </div>
    </div>
  )
}
