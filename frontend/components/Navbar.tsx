'use client'

import Link from 'next/link'
import { useAuth } from '@/components/providers/AuthProvider'
import { motion } from 'framer-motion'
import { TrendingUp, LogOut, User } from 'lucide-react'

export default function Navbar() {
  const { user, signOut } = useAuth()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-4 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
            <TrendingUp size={16} className="text-white" />
          </div>
          <span className="font-bold text-lg font-jakarta gradient-text">FinWise Teen</span>
        </Link>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link href="/dashboard">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  className="flex items-center gap-2 text-sm text-slate-300 hover:text-white px-4 py-2 rounded-lg hover:bg-white/5 transition-all"
                >
                  <User size={16} />
                  Dashboard
                </motion.button>
              </Link>
              <button
                onClick={signOut}
                className="flex items-center gap-2 text-sm text-slate-400 hover:text-white px-4 py-2 rounded-lg hover:bg-white/5 transition-all"
              >
                <LogOut size={14} />
                Sign Out
              </button>
            </>
          ) : (
            <>
              <Link href="/login">
                <button className="text-sm text-slate-300 hover:text-white px-4 py-2 rounded-lg hover:bg-white/5 transition-all">
                  Login
                </button>
              </Link>
              <Link href="/signup">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  className="btn-primary text-sm px-5 py-2"
                >
                  Get Started
                </motion.button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
