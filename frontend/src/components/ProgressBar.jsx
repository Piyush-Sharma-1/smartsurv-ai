export default function ProgressBar({ progress, status }) {
  const colors = {
    queued:     'bg-yellow-500',
    processing: 'bg-brand-500',
    completed:  'bg-green-400',
    failed:     'bg-red-500',
  }
  const bar = colors[status] || 'bg-gray-500'

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="capitalize font-mono text-gray-400">{status}</span>
        <span className="font-mono text-brand-500">{Math.round(progress)}%</span>
      </div>
      <div className="w-full bg-dark-700 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${bar}`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}