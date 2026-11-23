import ScoreCircle from './ScoreCircle'
import KeywordTags from './KeywordTags'

const HIRE_COLORS = {
  High: 'bg-green-900/50 text-green-400 border-green-700',
  Medium: 'bg-yellow-900/50 text-yellow-400 border-yellow-700',
  Low: 'bg-red-900/50 text-red-400 border-red-700',
}

const BREAKDOWN = [
  ['keyword_score', 'Keywords', 40],
  ['bullet_score', 'Bullet quality', 30],
  ['experience_score', 'Experience', 20],
  ['format_score', 'Format', 10],
]

function Breakdown({ breakdown }) {
  if (!breakdown) return null
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {BREAKDOWN.map(([key, label, max]) => {
        const value = breakdown[key] ?? 0
        return (
          <div key={key} className="bg-slate-900/60 rounded-xl p-4">
            <p className="text-xs text-slate-400">{label}</p>
            <p className="text-xl font-bold text-white">
              {Math.round(value)}<span className="text-sm text-slate-500">/{max}</span>
            </p>
            <div className="mt-2 h-1.5 rounded-full bg-slate-700">
              <div className="h-1.5 rounded-full bg-indigo-500" style={{ width: `${Math.min(100, (value / max) * 100)}%` }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function BulletReview({ b }) {
  const weak = b.score < 6
  return (
    <div className="space-y-2">
      <div className={`p-4 rounded-xl border ${weak ? 'bg-red-900/20 border-red-800/50' : 'bg-slate-900/40 border-slate-700'}`}>
        <p className={`text-xs font-medium mb-1 ${weak ? 'text-red-400' : 'text-green-400'}`}>
          {weak ? 'NEEDS WORK' : 'GOOD'} · {b.score}/10
        </p>
        <p className="text-sm text-slate-300 leading-relaxed">{b.original}</p>
        {b.issues?.length > 0 && (
          <ul className="mt-2 text-xs text-slate-400 list-disc list-inside">
            {b.issues.map((issue, i) => <li key={i}>{issue}</li>)}
          </ul>
        )}
      </div>
      {b.improved && (
        <div className="p-4 rounded-xl bg-green-900/20 border border-green-800/50">
          <p className="text-xs text-green-400 font-medium mb-1">SUGGESTED REWRITE</p>
          <p className="text-sm text-slate-300 leading-relaxed">{b.improved}</p>
          {/\[[^\]]+\]/.test(b.improved) && (
            <p className="text-xs text-slate-500 mt-2">Replace the [brackets] with your real numbers. Don't guess.</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function ResultCard({ result, onScanAgain }) {
  const bullets = [...(result.bullet_analysis ?? [])].sort((a, b) => a.score - b.score)
  return (
    <div className="w-full space-y-8 pb-16">
      <div className="bg-slate-800 rounded-2xl p-8 space-y-6">
        <div className="flex flex-col sm:flex-row items-center gap-8">
          <ScoreCircle score={result.ats_score} />
          <div className="flex-1 space-y-2 text-center sm:text-left">
            <h2 className="text-3xl font-bold text-white">{result.job_title}</h2>
            {result.hire_probability && (
              <span className={`inline-block px-4 py-1 rounded-full text-sm font-semibold border ${HIRE_COLORS[result.hire_probability] ?? ''}`}>
                Shortlist chance: {result.hire_probability}
              </span>
            )}
          </div>
        </div>
        <Breakdown breakdown={result.score_breakdown} />
        {result.overall_feedback && (
          <p className="text-slate-300 text-base leading-relaxed whitespace-pre-line">{result.overall_feedback}</p>
        )}
      </div>

      <div className="bg-slate-800 rounded-2xl p-8">
        <h3 className="text-lg font-semibold text-white mb-4">
          Keywords {result.match_percentage != null && <span className="text-slate-400 font-normal">· {result.match_percentage}% matched</span>}
        </h3>
        <KeywordTags matched={result.matched_keywords} missing={result.missing_keywords} />
      </div>

      {bullets.length > 0 && (
        <div className="bg-slate-800 rounded-2xl p-8 space-y-5">
          <h3 className="text-lg font-semibold text-white">Bullet Review</h3>
          {bullets.map((b, i) => <BulletReview key={i} b={b} />)}
        </div>
      )}

      <button
        onClick={onScanAgain}
        className="w-full py-5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xl transition-colors"
      >
        Scan Another Resume
      </button>
    </div>
  )
}
