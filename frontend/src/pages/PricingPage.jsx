import { motion } from 'framer-motion'
import { Rocket } from 'lucide-react'

export default function PricingPage() {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center min-h-[50vh] space-y-6 text-center px-6"
    >
      <Rocket className="w-8 h-8 text-ink-muted" />
      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-ink tracking-tight">Capacity Upgrade Required</h2>
        <p className="text-ink-muted text-sm max-w-sm mx-auto leading-relaxed">
          System currently operating in unrestricted beta mode. Tiered resource allocation structures will be implemented shortly.
        </p>
      </div>
    </motion.div>
  )
}
