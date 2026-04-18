import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ChevronDown, ChevronRight, History } from 'lucide-react'
import { getUserScans } from '../firebase/firestore'
import { cn } from '../utils/cn'

function formatDate(ts) {
  if (!ts) return ''
  const d = ts.toDate ? ts.toDate() : new Date(ts)
  return d.toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' })
}

const getScoreColor = (s) => {
  if (s >= 75) return 'text-truth-green'
  if (s >= 40) return 'text-truth-amber'
  return 'text-truth-red'
}

export default function HistoryPage({ user }) {
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    getUserScans(user.uid).then((data) => {
      setScans(data)
      setLoading(false)
    })
  }, [user.uid])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh]">
        <div className="w-6 h-6 border-2 border-clarity border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-ink-muted text-sm">Retrieving ledger...</p>
      </div>
    )
  }

  if (scans.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <History className="w-8 h-8 text-ink-muted" />
        <p className="text-ink-muted text-sm">No analysis records found.</p>
        <button
          onClick={() => navigate('/scan')}
          className="text-clarity hover:text-blue-400 text-sm font-medium transition-colors"
        >
          Initiate your first scan
        </button>
      </div>
    )
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="py-12 px-6 w-full max-w-4xl mx-auto"
    >
      <div className="mb-10">
        <h1 className="text-2xl font-semibold text-ink tracking-tight mb-2">Analysis Ledger</h1>
        <p className="text-ink-muted text-sm">Chronological record of your objective evaluations.</p>
      </div>

      <div className="flex flex-col border border-white/[0.04] rounded-lg overflow-hidden bg-surface">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-4 border-b border-white/[0.04] bg-void/50 text-xs font-medium text-ink-muted uppercase tracking-widest">
          <div className="col-span-3">Date</div>
          <div className="col-span-6">Target Role</div>
          <div className="col-span-2 text-right">Score</div>
          <div className="col-span-1"></div>
        </div>

        {/* Ledger Rows */}
        <div className="flex flex-col divide-y divide-white/[0.04]">
          {scans.map((scan) => {
            const isExpanded = expandedId === scan.id
            
            return (
              <div key={scan.id} className="flex flex-col group transition-colors hover:bg-white/[0.01]">
                <div 
                  className="grid grid-cols-12 gap-4 px-6 py-4 items-center cursor-pointer"
                  onClick={() => setExpandedId(isExpanded ? null : scan.id)}
                >
                  <div className="col-span-3 text-sm text-ink-muted font-data">
                    {formatDate(scan.createdAt)}
                  </div>
                  <div className="col-span-6 text-sm text-ink font-medium truncate pr-4">
                    {scan.jobTitle || 'Analysis'}
                  </div>
                  <div className={cn("col-span-2 text-right text-sm font-data", getScoreColor(scan.ats_score))}>
                    {scan.ats_score}%
                  </div>
                  <div className="col-span-1 flex justify-end text-ink-muted">
                    <motion.div animate={{ rotate: isExpanded ? 180 : 0 }}>
                      <ChevronDown className="w-4 h-4" />
                    </motion.div>
                  </div>
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-6 pt-2 border-t border-white/[0.02] bg-void/30">
                        <div className="flex flex-col md:flex-row gap-8">
                          
                          <div className="flex-1 space-y-3">
                            <h4 className="text-xs font-medium text-ink-muted uppercase tracking-widest">Critical Missing Keywords</h4>
                            <div className="flex flex-wrap gap-2">
                              {scan.missing_keywords?.slice(0, 5).map((kw, i) => (
                                <span key={i} className="px-2 py-1 bg-truth-red/10 text-truth-red text-xs font-medium rounded">
                                  {kw}
                                </span>
                              )) || <span className="text-xs text-ink-muted">No data recorded.</span>}
                              {scan.missing_keywords?.length > 5 && (
                                <span className="text-xs text-ink-muted px-2 py-1">+{scan.missing_keywords.length - 5} more</span>
                              )}
                            </div>
                          </div>

                          <div className="flex flex-col items-start justify-center gap-2">
                             <button
                              onClick={(e) => {
                                e.stopPropagation()
                                navigate('/result', { state: { result: scan } })
                              }}
                              className="text-xs font-medium text-clarity hover:text-blue-400 transition-colors flex items-center gap-1"
                            >
                              Review Full Report
                              <ChevronRight className="w-3 h-3" />
                            </button>
                          </div>

                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}
