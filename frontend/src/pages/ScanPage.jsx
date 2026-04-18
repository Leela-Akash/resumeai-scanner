import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { FileUp, FileText, ChevronRight, AlertCircle } from 'lucide-react'
import api from '../utils/api'
import { cn } from '../utils/cn'

export default function ScanPage() {
  const [file, setFile] = useState(null)
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

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
    if (!file) return setError('A PDF document is required for analysis.')
    if (!jd.trim()) return setError('Target job description is required.')
    setError('')
    setLoading(true)
    
    try {
      const form = new FormData()
      form.append('resume', file)
      form.append('job_description', jd)
      const { data } = await api.post('/api/analyze', form)
      navigate('/result', { state: { result: data } })
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'System error during analysis.')
      setLoading(false)
    }
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center py-12 px-6 w-full max-w-5xl mx-auto"
    >
      <div className="w-full mb-8">
        <h1 className="text-2xl font-semibold text-ink tracking-tight mb-2">Initiate Analysis</h1>
        <p className="text-ink-muted text-sm">Provide your current resume and the target job description.</p>
      </div>

      <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Upload Zone */}
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-ink-muted">Document (PDF)</label>
          <div
            {...getRootProps()}
            className={cn(
              "relative flex flex-col items-center justify-center h-64 bg-surface border border-white/[0.04] rounded-lg cursor-pointer transition-all overflow-hidden",
              isDragActive && "border-clarity/50 bg-surface/80",
              file && "border-white/[0.1]"
            )}
          >
            <input {...getInputProps()} />
            
            <AnimatePresence mode="wait">
              {file ? (
                <motion.div 
                  key="file"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center text-center p-6"
                >
                  <FileText className="w-10 h-10 text-truth-green mb-3" />
                  <p className="text-ink font-medium text-sm truncate max-w-xs">{file.name}</p>
                  <p className="text-ink-muted text-xs mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </motion.div>
              ) : (
                <motion.div 
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center text-center p-6"
                >
                  <FileUp className={cn("w-8 h-8 mb-3 transition-colors", isDragActive ? "text-clarity" : "text-ink-muted")} />
                  <p className="text-ink text-sm font-medium">Drop your resume</p>
                  <p className="text-ink-muted text-xs mt-1">PDF format only</p>
                </motion.div>
              )}
            </AnimatePresence>

            {loading && (
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ duration: 15, ease: "linear" }}
                className="absolute top-0 left-0 h-[2px] bg-clarity"
              />
            )}
          </div>
        </div>

        {/* Job Description Zone */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-ink-muted">Target Context</label>
            <span className="text-xs font-data text-ink-muted">{jd.length} chars</span>
          </div>
          <textarea
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            disabled={loading}
            placeholder="Paste the target job description here..."
            className="w-full h-64 bg-surface border border-white/[0.04] rounded-lg p-4 text-ink placeholder:text-ink-muted/50 resize-none focus:outline-none focus:border-clarity/50 transition-colors text-sm leading-relaxed"
          />
        </div>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="w-full mt-6"
          >
            <div className="flex items-center gap-2 p-4 bg-truth-red/10 border border-truth-red/20 rounded-lg text-truth-red text-sm font-medium">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="w-full mt-8 flex justify-end">
        <button
          onClick={handleAnalyze}
          disabled={loading || !file || !jd.trim()}
          className="relative px-8 py-3 bg-clarity text-white font-medium rounded text-sm transition-all hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 overflow-hidden"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              Processing...
            </span>
          ) : (
            <>
              Execute Scan
              <ChevronRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

    </motion.div>
  )
}
