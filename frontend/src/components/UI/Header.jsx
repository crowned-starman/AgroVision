import './Header.css'

export default function Header() {
  return (
    <header className="header">
      <div className="header-brand">
        <span className="header-logo">🌾</span>
        <span className="header-title">AgroVision</span>
        <span className="header-subtitle">Plataforma de Compatibilidad Agrícola</span>
      </div>
      <div className="header-badge">Datos simulados</div>
    </header>
  )
}
