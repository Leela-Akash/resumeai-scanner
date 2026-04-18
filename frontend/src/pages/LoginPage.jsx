import { signInWithGoogle } from '../firebase/auth'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async () => {
    setLoading(true)
    setError('')
    try {
      await signInWithGoogle()
    } catch (err) {
      setError(err.message || 'Authentication failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-[calc(100vh-64px)] bg-void flex flex-col items-center justify-center px-6 relative"
    >
      <div className="absolute top-8 left-8">
        <Link to="/" className="text-ink-muted hover:text-ink transition-colors flex items-center gap-2 text-sm font-medium">
          <ArrowLeft className="w-4 h-4" />
          Return
        </Link>
      </div>

      <div className="w-full max-w-[400px]">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-ink tracking-tight mb-2">Identify yourself</h1>
          <p className="text-ink-muted text-sm leading-relaxed">
            Secure access required to process your documents and store historical analysis.
          </p>
        </div>

        <div className="bg-surface border border-white/[0.04] rounded-lg p-6 space-y-6">
          {error && (
            <div className="p-3 bg-truth-red/10 border border-truth-red/20 rounded text-truth-red text-sm font-medium">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <button
              onClick={handleLogin}
              disabled={loading}
              className="w-full py-3 px-4 rounded bg-ink hover:bg-white disabled:opacity-50 text-void font-medium text-sm transition-colors flex items-center justify-center gap-3"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-void border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
              )}
              {loading ? 'Authenticating...' : 'Authenticate via Google'}
            </button>
          </div>
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-ink-muted">
            By proceeding, you agree to the systemic handling of your data.
          </p>
        </div>
      </div>
    </motion.div>
  )
}
