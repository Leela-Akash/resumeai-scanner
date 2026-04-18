import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import api from '../utils/api'

export default function UploadSection({ onResult }) {
  const [file, setFile] = useState(null)
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const onDrop = useCallback((accepted) => {
    setFile(accepted[0])
    setError('')
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const handleAnalyze = async () => {
    if (!file) return setError('Please upload a PDF resume.')
    if (!jd.trim()) return setError('Please paste a job description.')
    setError('')
    setLoading(true)
    try {
      const form = new FormData()
      form.append('resume', file)
      form.append('job_description', jd)
      const { data } = await api.post('/api/analyze', form)
      onResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full space-y-6">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors min-h-[200px] flex flex-col items-center justify-center
          ${isDragActive ? 'border-indigo-400 bg-indigo-900/20' : 'border-slate-600 hover:border-indigo-500 bg-slate-800/50'}`}
      >
        <input {...getInputProps()} />
        <div className="text-5xl mb-4">📄</div>
        {file ? (
          <p className="text-green-400 font-semibold text-lg">{file.name}</p>
        ) : (
          <>
            <p className="text-slate-300 font-semibold text-lg">Drag & drop your resume PDF here</p>
            <p className="text-slate-500 text-sm mt-2">or click to browse — PDF only, max 5MB</p>
          </>
        )}
      </div>

      <textarea
        value={jd}
        onChange={(e) => setJd(e.target.value)}
        placeholder="Paste the job description here..."
        className="w-full min-h-[150px] bg-slate-800 border border-slate-600 rounded-2xl p-5 text-slate-200 placeholder-slate-500 resize-y focus:outline-none focus:border-indigo-500 transition-colors text-base leading-relaxed"
      />

      {error && <p className="text-red-400 text-sm text-center">{error}</p>}

      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="w-full py-5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white font-bold text-xl transition-colors flex items-center justify-center gap-3"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Analyzing...
          </>
        ) : (
          '⚡ Analyze Now'
        )}
      </button>
    </div>
  )
}
