import { useState } from 'react'
import api from '../utils/api'

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: '/month',
    features: ['3 scans per month', 'ATS score', 'Keyword analysis', 'Bullet improvements'],
    cta: 'Current Plan',
    ctaStyle: 'bg-slate-700 text-slate-400 cursor-not-allowed',
    plan: null,
    highlight: false,
  },
  {
    name: 'Pro',
    price: '$9',
    period: '/month',
    features: ['Unlimited scans', 'Everything in Free', 'Full scan history', 'PDF report download', 'Priority support'],
    cta: 'Upgrade to Pro',
    ctaStyle: 'bg-gradient-to-r from-indigo-600 to-blue-500 hover:from-indigo-500 hover:to-blue-400 text-white',
    plan: 'pro',
    highlight: true,
  },
  {
    name: 'Premium',
    price: '$19',
    period: '/month',
    features: ['Everything in Pro', 'AI cover letter generation', 'LinkedIn optimization', 'Priority support'],
    cta: 'Get Premium',
    ctaStyle: 'bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-500 hover:to-pink-400 text-white',
    plan: 'premium',
    highlight: false,
  },
]

export default function PricingPage() {
  const [loading, setLoading] = useState(null)
  const [error, setError] = useState('')

  const handleCheckout = async (plan) => {
    if (!plan) return
    setLoading(plan)
    setError('')
    try {
      const { data } = await api.post('/api/create-checkout-session', { plan })
      window.location.href = data.url
    } catch {
      setError('Failed to start checkout. Please try again.')
      setLoading(null)
    }
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-extrabold text-white">Simple Pricing</h2>
        <p className="text-slate-400">Start free. Upgrade when you need more.</p>
      </div>

      {error && <p className="text-red-400 text-center text-sm">{error}</p>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((p) => (
          <div
            key={p.name}
            className={`relative bg-slate-800 rounded-2xl p-7 flex flex-col gap-6 border transition-colors
              ${p.highlight ? 'border-indigo-500 shadow-lg shadow-indigo-500/20' : 'border-slate-700'}`}
          >
            {p.highlight && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-500 text-white text-xs font-bold px-4 py-1 rounded-full">
                MOST POPULAR
              </div>
            )}
            <div>
              <p className="text-slate-400 text-sm font-medium">{p.name}</p>
              <div className="flex items-end gap-1 mt-1">
                <span className="text-4xl font-extrabold text-white">{p.price}</span>
                <span className="text-slate-400 mb-1">{p.period}</span>
              </div>
            </div>
            <ul className="space-y-3 flex-1">
              {p.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                  <span className="text-green-400 font-bold">✓</span> {f}
                </li>
              ))}
            </ul>
            <button
              disabled={!p.plan || loading === p.plan}
              onClick={() => handleCheckout(p.plan)}
              className={`w-full py-3.5 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-2 ${p.ctaStyle}`}
            >
              {loading === p.plan ? (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
              ) : p.cta}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
