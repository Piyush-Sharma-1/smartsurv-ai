import { useState } from 'react'
import VideoUpload from './components/VideoUpload'
import Dashboard from './components/Dashboard'

export default function App() {
  const [activeJob, setActiveJob] = useState(null)   // { jobId, filename }
  const [jobs, setJobs]           = useState([])

  const handleJobStarted = (jobId, filename) => {
    const job = { jobId, filename }
    setJobs(prev => [job, ...prev])
    setActiveJob(job)
  }

  return (
    <div className="min-h-screen bg-dark-900 text-gray-100 font-sans">
      {/* ── Header ── */}
      <header className="border-b border-dark-700 bg-dark-800/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-brand-500 rounded-lg flex items-center justify-center text-xl">
              👁
            </div>
            <div>
              <h1 className="font-bold text-white text-lg leading-none">SmartSurv AI</h1>
              <p className="text-gray-500 text-xs font-mono">surveillance analytics</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
            <span className="text-gray-400 text-sm font-mono">live</span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* ── Left: Upload + Job List ── */}
          <aside className="lg:col-span-1 space-y-6">
            <div>
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Upload Video
              </h2>
              <VideoUpload onJobStarted={handleJobStarted} />
            </div>

            {jobs.length > 0 && (
              <div>
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  Recent Jobs
                </h2>
                <div className="space-y-2">
                  {jobs.map(j => (
                    <button
                      key={j.jobId}
                      onClick={() => setActiveJob(j)}
                      className={`w-full text-left p-3 rounded-xl border transition-all ${
                        activeJob?.jobId === j.jobId
                          ? 'bg-brand-900/30 border-brand-500/50 text-brand-400'
                          : 'bg-dark-800 border-dark-600 text-gray-400 hover:border-dark-500 hover:text-white'
                      }`}
                    >
                      <p className="text-sm font-medium truncate">{j.filename}</p>
                      <p className="text-xs font-mono text-gray-600 mt-0.5 truncate">{j.jobId}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </aside>

          {/* ── Right: Dashboard ── */}
          <section className="lg:col-span-2">
            {activeJob ? (
              <Dashboard jobId={activeJob.jobId} filename={activeJob.filename} />
            ) : (
              <div className="flex flex-col items-center justify-center h-full min-h-[400px]
                              bg-dark-800 rounded-2xl border border-dashed border-dark-600 text-center p-8">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-xl font-semibold text-gray-300 mb-2">
                  No analysis yet
                </h3>
                <p className="text-gray-500 max-w-sm">
                  Upload a surveillance video on the left to detect objects,
                  track people, and identify anomalies automatically.
                </p>
                <div className="mt-6 grid grid-cols-3 gap-3 text-center">
                  {['🎯 Detect', '🔗 Track', '⚠️ Alert'].map(f => (
                    <div key={f} className="px-3 py-2 bg-dark-700 rounded-lg text-sm text-gray-400">{f}</div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}