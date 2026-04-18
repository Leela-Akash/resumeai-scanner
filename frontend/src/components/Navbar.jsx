import { Link, NavLink, useLocation } from 'react-router-dom'
import { logout } from '../firebase/auth'
import { LogOut } from 'lucide-react'

export default function Navbar({ user }) {
  const location = useLocation()

  if (!user) {
    return (
      <nav className="w-full h-16 border-b border-white/[0.04] bg-void/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
        <Link to="/" className="text-lg font-medium text-ink tracking-tight">
          GetShortlisted
        </Link>
        <Link to="/login" className="text-sm font-medium text-ink-muted hover:text-ink transition-colors">
          Sign In
        </Link>
      </nav>
    )
  }

  return (
    <nav className="w-full h-16 border-b border-white/[0.04] bg-void/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      <Link to="/" className="text-lg font-medium text-ink tracking-tight">
        GetShortlisted
      </Link>

      <div className="flex items-center gap-8">
        <div className="flex items-center gap-6">
          <NavLink 
            to="/scan"
            className={({ isActive }) => `
              text-sm font-medium pb-1 border-b transition-colors
              ${isActive ? 'text-ink border-ink' : 'text-ink-muted border-transparent hover:text-ink'}
            `}
          >
            Scan
          </NavLink>
          <NavLink 
            to="/history"
            className={({ isActive }) => `
              text-sm font-medium pb-1 border-b transition-colors
              ${isActive ? 'text-ink border-ink' : 'text-ink-muted border-transparent hover:text-ink'}
            `}
          >
            History
          </NavLink>
        </div>

        <div className="flex items-center gap-4 pl-8 border-l border-white/[0.04]">
          <div className="flex items-center gap-2">
            {user.photoURL ? (
              <img src={user.photoURL} alt="avatar" className="w-6 h-6 rounded-sm grayscale opacity-80" />
            ) : (
              <div className="w-6 h-6 rounded-sm bg-surface flex items-center justify-center text-xs font-data text-ink-muted">
                {user.email?.[0].toUpperCase()}
              </div>
            )}
            <span className="text-sm text-ink-muted hidden sm:block">
              {user.displayName?.split(' ')[0] || 'User'}
            </span>
          </div>
          <button
            onClick={logout}
            className="text-ink-muted hover:text-truth-red transition-colors p-1"
            title="Log out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </nav>
  )
}
