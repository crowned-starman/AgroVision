import './CropScoreCard.css'

const LEVEL_CONFIG = {
  alto:         { color: '#166534', bg: '#dcfce7', border: '#86efac', emoji: '✅' },
  medio:        { color: '#854d0e', bg: '#fef9c3', border: '#fde047', emoji: '🟡' },
  bajo:         { color: '#9a3412', bg: '#ffedd5', border: '#fdba74', emoji: '⚠️' },
  incompatible: { color: '#991b1b', bg: '#fee2e2', border: '#fca5a5', emoji: '❌' },
}

const DIM_LABELS = {
  temperatura:      'Temperatura',
  precipitacion:    'Precipitación',
  ph_suelo:         'pH suelo',
  ndvi:             'NDVI',
  pendiente:        'Pendiente',
  textura_suelo:    'Textura suelo',
  carbono_organico: 'Carbono org.',
}

const SEVERITY_COLOR = {
  critical: '#dc2626',
  high:     '#d97706',
  medium:   '#ca8a04',
}

function ScoreBar({ value }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.7 ? '#276749' : value >= 0.5 ? '#d97706' : '#dc2626'
  return (
    <div className="score-bar-row">
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="score-bar-pct" style={{ color }}>{pct}%</span>
    </div>
  )
}

export default function CropScoreCard({ score, isExpanded, onToggle }) {
  const cfg = LEVEL_CONFIG[score.recommendation_level] ?? LEVEL_CONFIG.bajo
  const pct = Math.round(score.score_total * 100)

  return (
    <div
      className={`crop-card ${isExpanded ? 'expanded' : ''}`}
      style={{ borderColor: cfg.border }}
    >
      {/* Header de la tarjeta */}
      <button className="crop-card-header" onClick={onToggle}>
        <div className="crop-card-left">
          <span className="crop-level-emoji">{cfg.emoji}</span>
          <div>
            <div className="crop-name">{score.crop_name}</div>
            <div
              className="crop-level-badge"
              style={{ background: cfg.bg, color: cfg.color }}
            >
              {score.recommendation_level}
            </div>
          </div>
        </div>
        <div className="crop-card-right">
          <span className="crop-score-pct" style={{ color: cfg.color }}>{pct}%</span>
          <span className="crop-chevron">{isExpanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* Barra de score */}
      <div className="crop-card-bar">
        <div
          className="crop-card-bar-fill"
          style={{ width: `${pct}%`, background: cfg.color }}
        />
      </div>

      {/* Detalle expandido */}
      {isExpanded && (
        <div className="crop-card-detail">

          {/* Explicación */}
          <p className="crop-explanation">{score.explanation}</p>

          {/* Breakdown por dimensión */}
          {score.score_breakdown && Object.keys(score.score_breakdown).length > 0 && (
            <div className="breakdown-section">
              <div className="breakdown-title">Detalle por dimensión</div>
              {Object.entries(score.score_breakdown).map(([dim, val]) => (
                <div key={dim} className="breakdown-row">
                  <span className="breakdown-label">
                    {DIM_LABELS[dim] ?? dim}
                  </span>
                  <ScoreBar value={val} />
                </div>
              ))}
            </div>
          )}

          {/* Factores limitantes */}
          {score.limiting_factors?.length > 0 && (
            <div className="limiting-section">
              <div className="limiting-title">Factores limitantes</div>
              {score.limiting_factors.map((f, i) => (
                <div
                  key={i}
                  className="limiting-item"
                  style={{ borderLeftColor: SEVERITY_COLOR[f.severity] ?? '#9ca3af' }}
                >
                  <span
                    className="limiting-severity"
                    style={{ color: SEVERITY_COLOR[f.severity] ?? '#9ca3af' }}
                  >
                    {f.severity === 'critical' ? 'CRÍTICO' : f.severity === 'high' ? 'ALTO' : 'MEDIO'}
                  </span>
                  <span className="limiting-msg">{f.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
