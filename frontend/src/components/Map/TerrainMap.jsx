import { useEffect, useRef } from 'react'
import L from 'leaflet'
import '@geoman-io/leaflet-geoman-free'
import './TerrainMap.css'

// Fix al bug clásico de íconos de Leaflet con bundlers
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const INITIAL_VIEW = [20.6, -103.3]  // Guadalajara, Jalisco
const INITIAL_ZOOM = 11

export default function TerrainMap({ onPolygonDrawn, drawnPolygon }) {
  const mapRef     = useRef(null)
  const mapInst    = useRef(null)
  const layerRef   = useRef(null)

  // Inicializar mapa una sola vez
  useEffect(() => {
    if (mapInst.current) return

    const map = L.map(mapRef.current, {
      center: INITIAL_VIEW,
      zoom:   INITIAL_ZOOM,
      zoomControl: true,
    })

    // Capa base: OpenStreetMap (gratis, sin API key)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map)

    // Capa satelital (ESRI World Imagery, sin API key)
    const satellite = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { attribution: '© Esri', maxZoom: 19 }
    )

    // Control de capas
    L.control.layers(
      { 'Mapa': map._layers[Object.keys(map._layers)[0]], 'Satélite': satellite },
      {},
      { position: 'topright' }
    ).addTo(map)

    // Herramientas de dibujo (Geoman)
    map.pm.addControls({
      position:       'topleft',
      drawMarker:     false,
      drawCircle:     false,
      drawCircleMarker: false,
      drawPolyline:   false,
      drawText:       false,
      rotateMode:     false,
      cutPolygon:     false,
    })

    // Evento: polígono creado
    map.on('pm:create', (e) => {
      // Eliminar polígono anterior si existe
      if (layerRef.current) {
        map.removeLayer(layerRef.current)
      }

      const layer = e.layer
      layerRef.current = layer

      // Estilo del polígono dibujado
      layer.setStyle({
        color:       '#276749',
        weight:      2,
        fillColor:   '#48bb78',
        fillOpacity: 0.25,
      })

      const geojson = layer.toGeoJSON().geometry
      onPolygonDrawn(geojson)
    })

    // Evento: polígono editado
    map.on('pm:edit', (e) => {
      if (e.layer === layerRef.current) {
        const geojson = e.layer.toGeoJSON().geometry
        onPolygonDrawn(geojson)
      }
    })

    mapInst.current = map

    return () => {
      map.remove()
      mapInst.current = null
    }
  }, [])

  // Limpiar polígono cuando el padre lo pide (drawnPolygon === null)
  useEffect(() => {
    if (!drawnPolygon && layerRef.current && mapInst.current) {
      mapInst.current.removeLayer(layerRef.current)
      layerRef.current = null
    }
  }, [drawnPolygon])

  return <div ref={mapRef} className="terrain-map" />
}
