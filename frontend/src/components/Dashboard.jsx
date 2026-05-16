import { useState, useEffect, useCallback } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, BarChart, Bar, ResponsiveContainer, Legend
} from 'recharts'
import { getJobStatus, getFrameData, BASE_URL } from '../api/client'
import StatsCard from './StatsCard'
import AnomalyAlerts from './AnomalyAlerts'
import ProgressBar from './ProgressBar'

const POLL_INTERVAL = 2500  // ms

export default function Dashboard({ jobId, filename }) {
  const [job,        setJob]        = useState(null)
  const [frameData,  setFrameData]  = useState([])
  const [activeTab,  setActiveTab]  = useState('overview')
  const [error,      setError]      = useState(null)

  const poll = useCallback(async () => {
    try {
      const { data } = await getJobStatus(jobId)
      setJob(data)

      if (data.status === 'completed' && frameData.length === 0) {
        const fd = await getFrameData(jobId, 300)
        setFrameData(fd.data.frames || [])
      }
    } catch (e) {
      setError(e.message)
    }
  }, [jobId, frameData.length])

  useEffect(() => {
    poll()
    const interval = setInterval(() => {
      if (job?.status === 'completed' || job?.status === 'failed') return
      poll()
    }, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [poll, job?.status])

  if (error) return (
    <div className="p-6 bg-red-900/20 border border-red-500/40 rounded-xl text-red-400">
      Error: {error}
    </div>
  )

  if (!job) return (
    <div className="flex items-center justify-center py-20 text-gray-500">
      <div className="animate-spin text-4xl mr-3">⚙️</div>
      Loading job…
    </div>
  )

  const results  = job.results || {}
  const summary  = results.summary || {}
  const byType   = summary.by_type || {}
  const anomalyTypeData = Object.entries(byType).map(([name, count]) => ({ name, count }))

  const tabs = ['overview', 'charts', 'anomalies', 'video']

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-white truncate max-w-md">{filename}</h2>
          <p className="text-gray-500 text-sm font-mono">{jobId}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold font-mono ${
          job.status === 'completed' ? 'bg-green-900/50 text-green-400 border border-green-500/40' :
          job.status === 'failed'    ? 'bg-red-900/50 text-red-400 border border-red-500/40' :
          job.status === 'processing'? 'bg-blue-900/50 text-blue-400 border border-blue-500/40 animate-pulse' :
          'bg-yellow-900/50 text-yellow-400 border border-yellow-500/40'
        }`}>
          {job.status}
        </span>
      </div>

      {/* Progress */}
      {job.status !== 'completed' && job.status !== 'failed' && (
        <div className="mb-6">
          <ProgressBar progress={job.progress || 0} status={job.status} />
          {job.current_frame && (
            <p className="text-gray-600 text-xs mt-1 font-mono">
              Frame {job.current_frame} / ~{results.total_frames || '?'}
            </p>
          )}
        </div>
      )}

      {/* Failed state */}
      {job.status === 'failed' && (
        <div className="p-4 bg-red-900/20 border border-red-500/40 rounded-xl text-red-400">
          ❌ Processing failed: {job.error}
        </div>
      )}

      {/* Results */}
      {job.status === 'completed' && (
        <>
          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-dark-800 rounded-xl p-1 border border-dark-600">
            {tabs.map(t => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium capitalize transition-all ${
                  activeTab === t
                    ? 'bg-brand-500 text-white shadow-lg'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {/* ── Overview ── */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <StatsCard icon="🎬" label="Total Frames" value={results.total_frames ?? '—'} />
              <StatsCard icon="📐" label="Resolution"   value={results.resolution ?? '—'} />
              <StatsCard icon="⚡" label="Proc FPS"     value={`${results.proc_fps ?? 0}`} sub="frames/sec" />
              <StatsCard icon="⏱️" label="Duration"     value={`${results.duration_sec ?? 0}s`} />
              <StatsCard icon="🕐" label="Process Time" value={`${results.processing_time ?? 0}s`} />
              <StatsCard
                icon="⚠️"
                label="Anomalies"
                value={summary.total_anomalies ?? 0}
                accent={true}
                sub="total events detected"
              />
              {Object.entries(summary.by_type || {}).map(([type, count]) => (
                <StatsCard key={type} icon="🔍" label={type.replace('_', ' ')} value={count} />
              ))}
            </div>
          )}

          {/* ── Charts ── */}
          {activeTab === 'charts' && frameData.length > 0 && (
            <div className="space-y-6">
              <div className="bg-dark-800 rounded-xl border border-dark-600 p-4">
                <h3 className="text-gray-300 font-semibold mb-4">People Count Over Time</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={frameData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="frame" stroke="#6b7280" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                      labelStyle={{ color: '#9ca3af' }}
                    />
                    <Line type="monotone" dataKey="people_count" stroke="#22c55e" strokeWidth={2} dot={false} name="People" />
                    <Line type="monotone" dataKey="tracks"        stroke="#60a5fa" strokeWidth={1.5} dot={false} name="Tracks" />
                    <Legend />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-dark-800 rounded-xl border border-dark-600 p-4">
                <h3 className="text-gray-300 font-semibold mb-4">Motion Score Over Time</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={frameData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="frame" stroke="#6b7280" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} tickFormatter={v => `${(v*100).toFixed(0)}%`} />
                    <Tooltip
                      contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                      formatter={v => [`${(v*100).toFixed(1)}%`, 'Motion']}
                    />
                    <Line type="monotone" dataKey="motion_score" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {anomalyTypeData.length > 0 && (
                <div className="bg-dark-800 rounded-xl border border-dark-600 p-4">
                  <h3 className="text-gray-300 font-semibold mb-4">Anomaly Breakdown</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={anomalyTypeData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                      <XAxis dataKey="name" stroke="#6b7280" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                      <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* ── Anomalies ── */}
          {activeTab === 'anomalies' && (
            <div className="bg-dark-800 rounded-xl border border-dark-600 p-4">
              <h3 className="text-gray-300 font-semibold mb-4">
                Anomaly Log — {summary.total_anomalies ?? 0} events
              </h3>
              <AnomalyAlerts anomalyLog={summary.anomaly_log || []} />
            </div>
          )}

          {/* ── Video ── */}
          {activeTab === 'video' && job.video_url && (
            <div className="bg-dark-800 rounded-xl border border-dark-600 overflow-hidden">
              <p className="text-gray-400 text-sm p-3 font-mono border-b border-dark-600">
                Annotated Output
              </p>
              <video
                src={`${BASE_URL}${job.video_url}`}
                controls
                className="w-full"
                style={{ maxHeight: '60vh' }}
              />
              <div className="p-3 border-t border-dark-600">
                <a
                  href={`${BASE_URL}${job.video_url}`}
                  download
                  className="inline-flex items-center gap-2 px-4 py-2 bg-brand-500 hover:bg-brand-600 
                             text-white rounded-lg text-sm font-medium transition-colors"
                >
                  ⬇ Download Annotated Video
                </a>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}