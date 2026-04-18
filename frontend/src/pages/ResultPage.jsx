import { useLocation, Navigate, Link } from 'react-router-dom'
import { motion, useMotionValue, useTransform, animate } from 'framer-motion'
import { useEffect, useState } from 'react'
import { ArrowRight, ChevronLeft, Check, X } from 'lucide-react'
import { cn } from '../utils/cn'

export default function ResultPage() {
  const location = useLocation()
  const result = location.state?.result

  if (!result) return <Navigate to="/scan" />

  const [score, setScore] = useState(0)

  useEffect(() => {
    const controls = animate(0, result.ats_score, {
      duration: 2,
      ease: "easeOut",
      onUpdate: (val) => setScore(Math.round(val))
    })
    return controls.stop
  }, [result.ats_score])

  const getScoreColor = (s) => {
    if (s >= 75) return 'text-truth-green'
    if (s >= 40) return 'text-truth-amber'
    return 'text-truth-red'
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1, 
      transition: { staggerChildren: 0.3 }
    }
  }

  const sectionVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col py-12 px-6 w-full max-w-4xl mx-auto"
    >
      <div className="mb-12">
        <Link to="/scan" className="text-ink-muted hover:text-ink transition-colors flex items-center gap-2 text-sm font-medium w-fit">
          <ChevronLeft className="w-4 h-4" />
          New Analysis
        </Link>
      </div>

      <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-16">
        
        {/* Top: Score and Narrative */}
        <motion.section variants={sectionVariants} className="flex flex-col md:flex-row items-start gap-12 border-b border-surface pb-12">
          <div className="flex flex-col items-start gap-2 min-w-[120px]">
            <span className="text-xs font-medium text-ink-muted uppercase tracking-widest">ATS Match</span>
            <div className={cn("text-7xl font-data tracking-tighter", getScoreColor(score))}>
              {score}%
            </div>
            <div className="text-sm font-medium text-ink-muted mt-2">
              Probability: <span className="text-ink capitalize">{result.hire_probability.toLowerCase()}</span>
            </div>
          </div>
          
          <div className="flex-1 pt-2">
            <h1 className="text-2xl font-semibold text-ink mb-4">{result.job_title || 'Analysis Complete'}</h1>
            <p className="text-lg text-ink-muted leading-relaxed font-narrative">
              {result.overall_feedback}
            </p>
          </div>
        </motion.section>

        {/* Keywords */}
        <motion.section variants={sectionVariants} className="space-y-6 border-b border-surface pb-12">
          <h2 className="text-lg font-semibold text-ink tracking-tight">Keyword Density</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-truth-green flex items-center gap-2">
                <Check className="w-4 h-4" /> Matched Context
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.matched_keywords?.length > 0 ? result.matched_keywords.map((kw, i) => (
                  <span key={i} className="px-3 py-1 bg-truth-green/10 text-truth-green text-sm font-medium rounded">
                    {kw}
                  </span>
                )) : <span className="text-sm text-ink-muted">No keywords matched.</span>}
              </div>
            </div>
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-truth-red flex items-center gap-2">
                <X className="w-4 h-4" /> Missing Context
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.missing_keywords?.length > 0 ? result.missing_keywords.map((kw, i) => (
                  <span key={i} className="px-3 py-1 bg-truth-red/10 text-truth-red text-sm font-medium rounded">
                    {kw}
                  </span>
                )) : <span className="text-sm text-ink-muted">No missing keywords detected.</span>}
              </div>
            </div>
          </div>
        </motion.section>

        {/* Bullet Points */}
        <motion.section variants={sectionVariants} className="space-y-6">
          <h2 className="text-lg font-semibold text-ink tracking-tight">Structural Adjustments</h2>
          <div className="flex flex-col gap-6">
            {result.bullet_analysis?.length > 0 ? result.bullet_analysis.map((b, i) => (
              <div key={i} className="flex flex-col md:flex-row gap-4 p-5 bg-surface border border-white/[0.04] rounded-lg">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-ink-muted uppercase tracking-widest">Current Fragment</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      b.grade === 'A' ? 'bg-truth-green/20 text-truth-green' :
                      b.grade === 'B' ? 'bg-clarity/20 text-clarity' :
                      b.grade === 'C' ? 'bg-truth-amber/20 text-truth-amber' :
                      'bg-truth-red/20 text-truth-red'
                    }`}>Grade {b.grade}</span>
                  </div>
                  <p className="text-sm text-ink-muted leading-relaxed">{b.bullet}</p>
                  {b.issues?.length > 0 && (
                    <p className="text-xs text-truth-red/70">{b.issues.join(' · ')}</p>
                  )}
                </div>

                {b.improved && (
                  <>
                    <div className="flex items-center justify-center py-2 md:py-0 px-2 text-ink-muted">
                      <ArrowRight className="w-5 h-5 hidden md:block" />
                    </div>
                    <div className="flex-1 space-y-2">
                      <span className="text-xs font-medium text-truth-green uppercase tracking-widest">Optimized Structure</span>
                      <p className="text-sm text-ink leading-relaxed">{b.improved}</p>
                    </div>
                  </>
                )}
              </div>
            )) : (
              <p className="text-sm text-ink-muted">No structural weaknesses detected in bullet points.</p>
            )}
          </div>
        </motion.section>

      </motion.div>
    </motion.div>
  )
}
