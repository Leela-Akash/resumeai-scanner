import { logout } from '../firebase/auth'

export default function Navbar({ user, onNavigate, currentPage }) {
  return (
    <nav className="w-full bg-slate-800/80 backdrop-blur border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <button
        onClick={() => onNavigate('scan')}
        className="text-xl font-extrabold text-white tracking-tight"
      >
        Resume<span className="text-indigo-400">AI</span> Scanner
      </button>

      <div className="flex items-center gap-4">
        <button
          onClick={() => onNavigate('history')}
          className={`text-sm font-medium transition-colors ${
            currentPage === 'history' ? 'text-indigo-400' : 'text-slate-400 hover:text-white'
          }`}
        >
          History
        </button>
        <button
          onClick={() => onNavigate('pricing')}
          className={`text-sm font-medium transition-colors ${
            currentPage === 'pricing' ? 'text-indigo-400' : 'text-slate-400 hover:text-white'
          }`}
        >
          Pricing
        </button>

        <div className="flex items-center gap-3 ml-2 pl-4 border-l border-slate-700">
          {user.photoURL && (
            <img src={user.photoURL} alt="avatar" className="w-8 h-8 rounded-full" />
          )}
          <span className="text-sm text-slate-300 hidden sm:block">
            {user.displayName?.split(' ')[0]}
          </span>
          <button
            onClick={logout}
            className="text-xs text-slate-400 hover:text-red-400 transition-colors border border-slate-600 hover:border-red-500 px-3 py-1.5 rounded-lg"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}
