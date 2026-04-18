import ScoreCircle from './ScoreCircle'
import KeywordTags from './KeywordTags'

const HIRE_COLORS = {
  High: 'bg-green-900/50 text-green-400 border-green-700',
  Medium: 'bg-yellow-900/50 text-yellow-400 border-yellow-700',
  Low: 'bg-red-900/50 text-red-400 border-red-700',
}

export default function ResultCard({ result, onScanAgain }) {
  return (
    <div className="w-full space-y-8 pb-16">

      {/* Score + hire probability */}
      <div className="bg-slate-800 rounded-2xl p-8 flex flex-col sm:flex-row items-center gap-8">
        <ScoreCircle score={result.ats_score} />
        <div className="flex-1 space-y-2 text-center sm:text-left">
          <h2 className="text-3xl font-bold text-white">{result.job_title}</h2>
          <span className={`inline-block px-4 py-1 rounded-full text-sm font-semibold border ${HIRE_COLORS[result.hire_probability]}`}>
            Hire Probability: {result.hire_probability}
          </span>
          <p className="text-slate-400 text-base leading-relaxed">{result.overall_feedback}</p>
        </div>
      </div>

      {/* Keywords */}
      <div className="bg-slate-800 rounded-2xl p-8">
        <h3 className="text-lg font-semibold text-white mb-4">Keywords Analysis</h3>
        <KeywordTags matched={result.matched_keywords} missing={result.missing_keywords} />
      </div>

      {/* Bullets */}
      {result.bullet_analysis?.length > 0 && (
        <div className="bg-slate-800 rounded-2xl p-8 space-y-5">
          <h3 className="text-lg font-semibold text-white">Bullet Point Improvements</h3>
          {result.bullet_analysis.map((b, i) => (
            <div key={i} className="space-y-2">
              <div className="p-4 rounded-xl bg-red-900/20 border border-red-800/50">
                <p className="text-xs text-red-400 font-medium mb-1">WEAK — Grade {b.grade}</p>
                <p className="text-sm text-slate-300 leading-relaxed">{b.bullet}</p>
              </div>
              {b.improved && (
                <div className="p-4 rounded-xl bg-green-900/20 border border-green-800/50">
                  <p className="text-xs text-green-400 font-medium mb-1">IMPROVED</p>
                  <p className="text-sm text-slate-300 leading-relaxed">{b.improved}</p>
                </div>
              )}
            </div>
          ))}
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
