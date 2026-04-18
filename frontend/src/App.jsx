import { useState, useEffect } from 'react'
import { useAuth } from './hooks/useAuth'
import Navbar from './components/Navbar'
import UploadSection from './components/UploadSection'
import ResultCard from './components/ResultCard'
import LoginPage from './pages/LoginPage'
import HistoryPage from './pages/HistoryPage'
import PricingPage from './pages/PricingPage'
import { saveScan } from './firebase/firestore'

export default function App() {
  const { user, userData } = useAuth()
  const [result, setResult] = useState(null)
  const [currentPage, setCurrentPage] = useState('scan')
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [scansUsed, setScansUsed] = useState(null)

  useEffect(() => {
    const handler = () => setShowUpgradeModal(true)
    window.addEventListener('free-limit-reached', handler)
    return () => window.removeEventListener('free-limit-reached', handler)
  }, [])

  // Loading state
  if (user === undefined) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <svg className="animate-spin h-10 w-10 text-indigo-400" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
      </div>
    )
  }

  // Not logged in
  if (!user) return <LoginPage />

  const handleResult = async (data) => {
    await saveScan(user.uid, data)
    setScansUsed((prev) => (prev ?? userData?.scansUsed ?? 0) + 1)
    setResult(data)
    setCurrentPage('scan')
  }

  const handleAnalyzeRequest = () => {
    const used = scansUsed ?? userData?.scansUsed ?? 0
    if (userData?.plan === 'free' && used >= 3) {
      setShowUpgradeModal(true)
      return false
    }
    return true
  }

  const renderPage = () => {
    if (currentPage === 'history') return <HistoryPage user={user} onViewResult={(r) => { setResult(r); setCurrentPage('scan') }} />
    if (currentPage === 'pricing') return <PricingPage />
    return result
      ? <ResultCard result={result} onScanAgain={() => setResult(null)} />
      : <UploadSection onResult={handleResult} onAnalyzeRequest={handleAnalyzeRequest} />
  }

  return (
    <div className="min-h-screen bg-slate-900">
      <Navbar user={user} onNavigate={(page) => { setCurrentPage(page); setResult(null) }} currentPage={currentPage} />

      <div className="max-w-4xl mx-auto px-6 py-10">
        {currentPage === 'scan' && !result && (
          <div className="text-center mb-10">
            <h1 className="text-5xl font-extrabold text-white tracking-tight">
              Resume<span className="text-indigo-400">AI</span> Scanner
            </h1>
            <p className="text-slate-400 mt-3 text-xl">Get your ATS score in 10 seconds</p>
            {userData && (
              <p className="text-slate-500 mt-2 text-sm">
                {userData.plan === 'free'
                  ? (() => { const rem = 3 - (scansUsed ?? userData.scansUsed ?? 0); return `${rem} free scan${rem !== 1 ? 's' : ''} remaining` })()
                  : '✨ Pro — Unlimited scans'}
              </p>
            )}
          </div>
        )}
        {renderPage()}
      </div>

      {showUpgradeModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-slate-800 rounded-2xl p-8 max-w-md w-full text-center space-y-5 border border-slate-700">
            <div className="text-5xl">🚀</div>
            <h2 className="text-2xl font-bold text-white">You've used your 3 free scans!</h2>
            <p className="text-slate-400">Upgrade to Pro for unlimited scans and full history access.</p>
            <div className="bg-slate-700/50 rounded-xl p-4 text-left space-y-2 text-sm text-slate-300">
              <p>✅ Unlimited scans</p>
              <p>✅ Full scan history</p>
              <p>✅ PDF report download</p>
              <p>✅ Priority support</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => { setShowUpgradeModal(false); setCurrentPage('pricing') }}
                className="flex-1 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-colors"
              >
                Upgrade Now — $9/mo
              </button>
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="flex-1 py-3 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300 font-medium transition-colors"
              >
                Maybe Later
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
