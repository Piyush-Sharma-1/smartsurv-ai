const SEVERITY_STYLES = {
  HIGH:   { bg: 'bg-red-900/40',    border: 'border-red-500',   text: 'text-red-400',   badge: 'bg-red-500' },
  MEDIUM: { bg: 'bg-orange-900/30', border: 'border-orange-500', text: 'text-orange-400', badge: 'bg-orange-500' },
  LOW:    { bg: 'bg-yellow-900/20', border: 'border-yellow-600', text: 'text-yellow-400', badge: 'bg-yellow-500' },
}

const TYPE_ICONS = {
  RUNNING:          '🏃',
  LOITERING:        '🧍',
  CROWD_SURGE:      '👥',
  MASS_MOVEMENT:    '🌊',
  DIRECTION_CHANGE: '↩️',
}

export default function AnomalyAlerts({ anomalyLog = [] }) {
  if (!anomalyLog.length) {
    return (
      <div className="text-center py-10 text-gray-600">
        <div className="text-5xl mb-3">✅</div>
        <p>No anomalies detected</p>
      </div>
    )
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
      {anomalyLog.slice().reverse().map((a, i) => {
        const s = SEVERITY_STYLES[a.severity] || SEVERITY_STYLES.LOW
        return (
          <div key={i} className={`rounded-lg border p-3 ${s.bg} ${s.border}`}>
            <div className="flex items-start gap-3">
              <span className="text-lg">{TYPE_ICONS[a.type] || '⚠️'}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full text-white ${s.badge}`}>
                    {a.severity}
                  </span>
                  <span className={`text-sm font-semibold ${s.text} font-mono`}>
                    {a.type}
                  </span>
                  <span className="text-gray-500 text-xs font-mono ml-auto">
                    Frame #{a.frame}
                  </span>
                </div>
                <p className="text-gray-300 text-sm truncate">{a.description}</p>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}