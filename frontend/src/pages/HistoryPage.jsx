import { useEffect, useState } from 'react'
import { getUserScans } from '../firebase/firestore'

const SCORE_COLOR = (s) => s >= 75 ? 'text-green-400' : s >= 50 ? 'text-yellow-400' : 'text-red-400'
const HIRE_COLOR = { High: 'text-green-400', Medium: 'text-yellow-400', Low: 'text-red-400' }

function formatDate(ts) {
  if (!ts) return ''
  const d = ts.toDate ? ts.toDate() : new Date(ts)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function HistoryPage({ user, onViewResult }) {
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getUserScans(user.uid).then((data) => {
      setScans(data)
      setLoading(false)
    })
  }, [user.uid])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <svg className="animate-spin h-8 w-8 text-indigo-400" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
      </div>
    )
  }

  if (scans.length === 0) {
    return (
      <div className="text-center py-20 space-y-3">
        <div className="text-5xl">📭</div>
        <p className="text-slate-400 text-lg">No scans yet. Upload your first resume!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white mb-6">Scan History ({scans.length})</h2>
      {scans.map((scan) => (
        <div key={scan.id} className="bg-slate-800 rounded-2xl p-6 flex items-center justify-between gap-4 border border-slate-700 hover:border-slate-600 transition-colors">
          <div className="flex items-center gap-5">
            <div className="text-center min-w-[56px]">
              <p className={`text-3xl font-extrabold ${SCORE_COLOR(scan.ats_score)}`}>{scan.ats_score}</p>
              <p className="text-xs text-slate-500">ATS</p>
            </div>
            <div>
              <p className="text-white font-semibold text-lg">{scan.jobTitle}</p>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-slate-500 text-sm">{formatDate(scan.createdAt)}</span>
                <span className={`text-xs font-medium ${HIRE_COLOR[scan.hire_probability]}`}>
                  {scan.hire_probability} chance
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={() => onViewResult(scan)}
            className="shrink-0 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors"
          >
            View Result
          </button>
        </div>
      ))}
    </div>
  )
}
