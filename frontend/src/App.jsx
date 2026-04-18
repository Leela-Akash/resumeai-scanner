import { useState } from 'react'
import { useAuth } from './hooks/useAuth'
import Navbar from './components/Navbar'
import UploadSection from './components/UploadSection'
import ResultCard from './components/ResultCard'
import LoginPage from './pages/LoginPage'
import HistoryPage from './pages/HistoryPage'
import PricingPage from './pages/PricingPage'

export default function App() {
  const { user, userData } = useAuth()
  const [result, setResult] = useState(null)
  const [currentPage, setCurrentPage] = useState('scan')

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

  if (!user) return <LoginPage />

  const handleResult = (data) => {
    setResult(data)
    setCurrentPage('scan')
  }

  const renderPage = () => {
    if (currentPage === 'history') return <HistoryPage user={user} onViewResult={(r) => { setResult(r); setCurrentPage('scan') }} />
    if (currentPage === 'pricing') return <PricingPage />
    return result
      ? <ResultCard result={result} onScanAgain={() => setResult(null)} />
      : <UploadSection onResult={handleResult} />
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
          </div>
        )}
        {renderPage()}
      </div>
    </div>
  )
}
