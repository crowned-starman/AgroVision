import FeaturesSummary from './FeaturesSummary.jsx'
import CropScoreList from './CropScoreList.jsx'
import './ResultsPanel.css'

export default function ResultsPanel({ analysis }) {
  const topCrop = analysis.scores[0]

  return (
    <div className="results-panel">
      <div className="results-header">
        <h2>Resultados del análisis</h2>
        <span className="results-source">
          {analysis.data_source === 'mock' ? '⚠ Datos simulados' : '🛰 Sentinel-2'}
        </span>
      </div>

      {topCrop && topCrop.recommendation_level === 'alto' && (
        <div className="top-recommendation">
          <span className="top-label">Mejor opción</span>
          <span className="top-crop">{topCrop.crop_name}</span>
          <span className="top-score">{Math.round(topCrop.score_total * 100)}% compatible</span>
        </div>
      )}

      <FeaturesSummary features={analysis.features} />
      <CropScoreList scores={analysis.scores} />
    </div>
  )
}
