import { useState } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { useAuth } from './hooks/useAuth'

import Navbar from './components/Navbar'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import ScanPage from './pages/ScanPage'
import ResultPage from './pages/ResultPage'
import HistoryPage from './pages/HistoryPage'
import PricingPage from './pages/PricingPage'

export default function App() {
  const { user } = useAuth()
  const location = useLocation()
  
  if (user === undefined) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-clarity border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-void flex flex-col font-narrative text-ink selection:bg-clarity/30">
      <Navbar user={user} />

      <main className="flex-1 flex flex-col relative w-full h-full">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={!user ? <LandingPage /> : <Navigate to="/scan" />} />
            <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/scan" />} />
            <Route path="/scan" element={user ? <ScanPage /> : <Navigate to="/login" />} />
            <Route path="/result" element={user ? <ResultPage /> : <Navigate to="/login" />} />
            <Route path="/history" element={user ? <HistoryPage user={user} /> : <Navigate to="/login" />} />
            <Route path="/pricing" element={<PricingPage />} />
          </Routes>
        </AnimatePresence>
      </main>
    </div>
  )
}
