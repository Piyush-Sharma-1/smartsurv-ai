export default function StatsCard({ icon, label, value, sub, accent = false }) {
  return (
    <div className={`rounded-xl border p-4 ${
      accent
        ? 'bg-brand-900/30 border-brand-500/40'
        : 'bg-dark-800 border-dark-600'
    }`}>
      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-gray-400 text-sm">{label}</span>
      </div>
      <p className={`text-3xl font-bold font-mono ${accent ? 'text-brand-500' : 'text-white'}`}>
        {value}
      </p>
      {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
    </div>
  )
}