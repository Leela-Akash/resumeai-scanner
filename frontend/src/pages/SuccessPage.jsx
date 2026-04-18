import { useEffect, useState } from 'react'
import { doc, onSnapshot } from 'firebase/firestore'
import { db } from '../firebase/config'
import { auth } from '../firebase/config'

export default function SuccessPage({ onNavigate }) {
  const [plan, setPlan] = useState(null)

  useEffect(() => {
    const user = auth.currentUser
    if (!user) return

    // Listen for Firestore plan update (webhook may take a few seconds)
    const unsub = onSnapshot(doc(db, 'users', user.uid), (snap) => {
      if (snap.exists()) {
        setPlan(snap.data().plan)
      }
    })
    return unsub
  }, [])

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-6">
      <div className="bg-slate-800 rounded-2xl p-10 max-w-md w-full text-center space-y-6 border border-slate-700">
        <div className="text-6xl">🎉</div>
        <h1 className="text-3xl font-extrabold text-white">Payment Successful!</h1>
        <p className="text-slate-400">
          {plan && plan !== 'free'
            ? `Your ${plan.charAt(0).toUpperCase() + plan.slice(1)} plan is now active.`
            : 'Your plan is being activated, please wait a moment...'}
        </p>

        <div className="bg-slate-700/50 rounded-xl p-4 text-left space-y-2 text-sm text-slate-300">
          <p>✅ Unlimited scans unlocked</p>
          <p>✅ Full scan history saved</p>
          <p>✅ PDF report download enabled</p>
        </div>

        <button
          onClick={() => onNavigate('scan')}
          className="w-full py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-lg transition-colors"
        >
          Start Scanning →
        </button>
      </div>
    </div>
  )
}
