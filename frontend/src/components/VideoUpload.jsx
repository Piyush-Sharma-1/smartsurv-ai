import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadVideo } from '../api/client'

export default function VideoUpload({ onJobStarted }) {
  const [uploading, setUploading]   = useState(false)
  const [uploadPct, setUploadPct]   = useState(0)
  const [error, setError]           = useState(null)

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return
    setError(null)
    setUploading(true)
    setUploadPct(0)

    try {
      const { data } = await uploadVideo(file, setUploadPct)
      onJobStarted(data.job_id, file.name)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [onJobStarted])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm'] },
    maxFiles: 1,
    disabled: uploading,
  })

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer
          transition-all duration-300 group
          ${isDragActive
            ? 'border-brand-500 bg-brand-900/20 scale-[1.01]'
            : 'border-dark-600 bg-dark-800 hover:border-brand-500/60 hover:bg-dark-700'
          }
          ${uploading ? 'opacity-70 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />

        {/* Icon */}
        <div className={`text-6xl mb-4 transition-transform duration-300
          ${isDragActive ? 'scale-110' : 'group-hover:scale-105'}`}>
          {uploading ? '⏳' : isDragActive ? '📂' : '🎬'}
        </div>

        {uploading ? (
          <div>
            <p className="text-brand-500 font-semibold mb-3">Uploading...</p>
            <div className="w-48 mx-auto bg-dark-700 rounded-full h-2">
              <div
                className="h-full bg-brand-500 rounded-full transition-all"
                style={{ width: `${uploadPct}%` }}
              />
            </div>
            <p className="text-gray-500 text-sm mt-2 font-mono">{uploadPct}%</p>
          </div>
        ) : (
          <div>
            <p className="text-lg font-semibold text-gray-200 mb-1">
              {isDragActive ? 'Drop video here' : 'Drag & drop your video'}
            </p>
            <p className="text-gray-500 text-sm mb-4">or click to browse</p>
            <p className="text-gray-600 text-xs font-mono">
              MP4 · AVI · MOV · MKV · WebM — max 200 MB
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-400 text-sm">
          ⚠️ {error}
        </div>
      )}
    </div>
  )
}