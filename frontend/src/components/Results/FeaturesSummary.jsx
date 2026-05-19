import './FeaturesSummary.css'

const METRICS = [
  { key: 'ndvi_mean',        label: 'NDVI',          format: v => v.toFixed(2),        unit: '' },
  { key: 'temp_mean_c',      label: 'Temperatura',   format: v => v.toFixed(1),        unit: '°C' },
  { key: 'annual_precip_mm', label: 'Precipitación', format: v => Math.round(v),       unit: 'mm/año' },
  { key: 'ph_mean',          label: 'pH suelo',      format: v => v.toFixed(1),        unit: '' },
  { key: 'elevation_mean',   label: 'Elevación',     format: v => Math.round(v),       unit: 'm' },
  { key: 'slope_mean',       label: 'Pendiente',     format: v => v.toFixed(1),        unit: '°' },
  { key: 'clay_pct',         label: 'Arcilla',       format: v => Math.round(v),       unit: '%' },
  { key: 'organic_carbon',   label: 'Carbono org.',  format: v => v.toFixed(1),        unit: '%' },
]

function ndviColor(v) {
  if (v > 0.6) return '#276749'
  if (v > 0.35) return '#d97706'
  return '#dc2626'
}

export default function FeaturesSummary({ features }) {
  return (
    <div className="features-summary">
      <h3 className="features-title">Variables ambientales</h3>

      {/* NDVI destacado */}
      <div className="ndvi-card">
        <div className="ndvi-label">NDVI (actividad vegetal)</div>
        <div className="ndvi-bar-track">
          <div
            className="ndvi-bar-fill"
            style={{
              width: `${Math.round(features.ndvi_mean * 100)}%`,
              background: ndviColor(features.ndvi_mean),
            }}
          />
        </div>
        <div className="ndvi-range">
          <span style={{ color: ndviColor(features.ndvi_mean), fontWeight: 700 }}>
            {features.ndvi_mean.toFixed(3)}
          </span>
          <span className="ndvi-sub">
            min {features.ndvi_min.toFixed(2)} · máx {features.ndvi_max.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Grid de métricas */}
      <div className="metrics-grid">
        {METRICS.slice(1).map(m => (
          <div key={m.key} className="metric-tile">
            <span className="metric-label">{m.label}</span>
            <span className="metric-value">
              {features[m.key] != null ? m.format(features[m.key]) : '—'}
              {m.unit && <span className="metric-unit"> {m.unit}</span>}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
