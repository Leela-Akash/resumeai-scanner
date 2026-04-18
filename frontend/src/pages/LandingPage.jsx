import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowRight, CheckCircle2, ShieldCheck, FileText } from 'lucide-react'

export default function LandingPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { staggerChildren: 0.2, duration: 0.6, ease: "easeOut" }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
  }

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      exit={{ opacity: 0, transition: { duration: 0.3 } }}
      className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] px-6"
    >
      <div className="max-w-3xl text-center space-y-8">
        
        <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface border border-ink-muted/20 text-ink-muted text-sm font-narrative mb-4">
          <span className="w-2 h-2 rounded-full bg-truth-green"></span>
          System Operational. Ready for analysis.
        </motion.div>

        <motion.h1 variants={itemVariants} className="text-5xl md:text-7xl font-semibold tracking-tight text-ink">
          Objective truth for your <br />
          <span className="text-ink-muted">resume.</span>
        </motion.h1>

        <motion.p variants={itemVariants} className="text-lg md:text-xl text-ink-muted max-w-2xl mx-auto leading-relaxed">
          Upload your resume. Receive a clinical, unbiased analysis of your ATS compatibility. 
          No jargon, no fluff. Just actionable data to secure the interview.
        </motion.p>

        <motion.div variants={itemVariants} className="pt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link 
            to="/login"
            className="group relative inline-flex items-center justify-center px-8 py-3 bg-clarity text-white font-medium rounded-md overflow-hidden transition-all hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-clarity focus:ring-offset-2 focus:ring-offset-void w-full sm:w-auto"
          >
            <span className="mr-2">Initiate Scan</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <div className="text-sm text-ink-muted font-data tracking-tight">
            100% Free • No Credit Card
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16 border-t border-surface/50 mt-16 text-left">
          {[
            { icon: ShieldCheck, title: "Unbiased Scoring", desc: "Our engine strips away formatting to evaluate pure keyword density and semantic match." },
            { icon: FileText, title: "Surgical Precision", desc: "Side-by-side comparisons of weak bullet points versus optimized suggestions." },
            { icon: CheckCircle2, title: "Immediate Action", desc: "No complex dashboards. Get a clear checklist of what to fix, exactly where." }
          ].map((feature, i) => (
            <div key={i} className="p-6 bg-surface rounded-lg border border-white/[0.02]">
              <feature.icon className="w-6 h-6 text-ink-muted mb-4" />
              <h3 className="text-base font-medium text-ink mb-2">{feature.title}</h3>
              <p className="text-sm text-ink-muted leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </motion.div>

      </div>
    </motion.div>
  )
}
