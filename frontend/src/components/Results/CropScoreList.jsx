import { useState } from 'react'
import CropScoreCard from './CropScoreCard.jsx'
import './CropScoreList.css'

const LEVELS = ['todos', 'alto', 'medio', 'bajo', 'incompatible']

export default function CropScoreList({ scores }) {
  const [filter, setFilter]   = useState('todos')
  const [expanded, setExpanded] = useState(null)

  const visible = filter === 'todos'
    ? scores
    : scores.filter(s => s.recommendation_level === filter)

  const counts = {
    alto:          scores.filter(s => s.recommendation_level === 'alto').length,
    medio:         scores.filter(s => s.recommendation_level === 'medio').length,
    bajo:          scores.filter(s => s.recommendation_level === 'bajo').length,
    incompatible:  scores.filter(s => s.recommendation_level === 'incompatible').length,
  }

  return (
    <div className="crop-score-list">
      <div className="list-header">
        <h3>Compatibilidad por cultivo</h3>
        <span className="list-count">{scores.length} cultivos</span>
      </div>

      <div className="filter-tabs">
        {LEVELS.map(lvl => (
          <button
            key={lvl}
            className={`filter-tab ${filter === lvl ? 'active' : ''} tab-${lvl}`}
            onClick={() => setFilter(lvl)}
          >
            {lvl === 'todos' ? `Todos (${scores.length})` : `${lvl} (${counts[lvl] ?? 0})`}
          </button>
        ))}
      </div>

      <div className="cards-container">
        {visible.length === 0
          ? <p className="no-results">No hay cultivos en este nivel</p>
          : visible.map(score => (
            <CropScoreCard
              key={score.crop_id}
              score={score}
              isExpanded={expanded === score.crop_id}
              onToggle={() => setExpanded(expanded === score.crop_id ? null : score.crop_id)}
            />
          ))
        }
      </div>
    </div>
  )
}
