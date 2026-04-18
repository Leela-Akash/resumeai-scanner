export default function KeywordTags({ matched = [], missing = [] }) {
  return (
    <div className="space-y-3">
      <div>
        <p className="text-sm text-slate-400 mb-2">Matched Keywords</p>
        <div className="flex flex-wrap gap-2">
          {matched.map((kw) => (
            <span key={kw} className="px-3 py-1 rounded-full text-xs font-medium bg-green-900/50 text-green-400 border border-green-700">
              ✓ {kw}
            </span>
          ))}
        </div>
      </div>
      <div>
        <p className="text-sm text-slate-400 mb-2">Missing Keywords</p>
        <div className="flex flex-wrap gap-2">
          {missing.map((kw) => (
            <span key={kw} className="px-3 py-1 rounded-full text-xs font-medium bg-red-900/50 text-red-400 border border-red-700">
              ✗ {kw}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
