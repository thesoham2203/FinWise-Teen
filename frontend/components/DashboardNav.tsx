'use client'

import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { TrendingUp, LayoutDashboard, User, LogOut, Settings } from 'lucide-react'
import { useAuth } from '@/components/providers/AuthProvider'

const navLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/profile', label: 'Profile', icon: User },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export default function DashboardNav() {
  const { user, signOut } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  const handleSignOut = async () => {
    await signOut()
    router.push('/')
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5" style={{ background: 'rgba(8,11,20,0.9)', backdropFilter: 'blur(16px)' }}>
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
            <TrendingUp size={14} className="text-white" />
          </div>
          <span className="font-bold font-jakarta gradient-text text-sm">FinWise Teen</span>
        </Link>

        <div className="flex items-center gap-1">
          {navLinks.map(link => (
            <Link key={link.href} href={link.href}>
              <button className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg transition-all ${
                pathname === link.href
                  ? 'bg-indigo-500/15 text-indigo-300'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}>
                <link.icon size={14} />
                <span className="hidden md:block">{link.label}</span>
              </button>
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:block text-xs text-slate-500">
            {user?.email?.split('@')[0]}
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            onClick={handleSignOut}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white px-3 py-2 rounded-lg hover:bg-white/5 transition-all"
          >
            <LogOut size={14} />
          </motion.button>
        </div>
      </div>
    </nav>
  )
}
