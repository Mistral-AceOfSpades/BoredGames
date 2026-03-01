import { Link, useLocation } from 'react-router-dom';
import { Dice5, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/search', label: 'Find Game' },
  { to: '/upload', label: 'Upload Rulebook' },
  { to: '/games', label: 'My Games' },
];

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { pathname } = useLocation();
  const { user, login, logout, isAuthenticated } = useAuth();

  return (
    <nav className="border-b border-game-border bg-game-card/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <Dice5 className="h-8 w-8 text-brand-500 group-hover:text-brand-400 transition-colors" />
            <span className="font-display text-xl font-bold text-white">BoredGames</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`text-sm font-medium transition-colors ${
                  pathname === link.to
                    ? 'text-brand-400'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            ))}
            <div className="ml-4 border-l border-game-border pl-4">
              {isAuthenticated ? (
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-300">{user?.username}</span>
                  <button onClick={logout} className="text-sm text-gray-400 hover:text-white">
                    Sign Out
                  </button>
                </div>
              ) : (
                <button onClick={login} className="btn-primary text-sm py-1.5 px-4">
                  Sign In
                </button>
              )}
            </div>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden text-gray-400 hover:text-white"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="md:hidden border-t border-game-border bg-game-card">
          <div className="px-4 py-3 space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMobileOpen(false)}
                className={`block py-2 text-sm font-medium ${
                  pathname === link.to ? 'text-brand-400' : 'text-gray-400'
                }`}
              >
                {link.label}
              </Link>
            ))}
            {isAuthenticated ? (
              <button onClick={logout} className="block py-2 text-sm text-gray-400">
                Sign Out ({user?.username})
              </button>
            ) : (
              <button onClick={login} className="btn-primary w-full text-sm py-2 mt-2">
                Sign In
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
