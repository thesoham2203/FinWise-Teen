'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { TrendingUp, Chrome } from 'lucide-react'
import { supabase } from '@/lib/supabase'

export default function SignupPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: name } },
    })
    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      setSuccess(true)
      setTimeout(() => router.push('/onboard'), 1500)
    }
  }

  const handleGoogleSignup = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/onboard` },
    })
  }

  if (success) {
    return (
      <div className="min-h-screen bg-[#080B14] flex items-center justify-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center"
        >
          <div className="text-5xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold mb-2">Account Created!</h2>
          <p className="text-slate-400">Setting up your financial profile...</p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#080B14] flex items-center justify-center px-4 relative">
      <div className="hero-orb w-[400px] h-[400px] bg-violet-600/15 -top-20 right-0" />
      <div className="hero-orb w-[300px] h-[300px] bg-indigo-600/10 bottom-0 -left-20" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="glass-card p-8">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <TrendingUp size={16} />
            </div>
            <span className="font-bold font-jakarta gradient-text">FinWise Teen</span>
          </div>

          <h1 className="text-2xl font-bold font-jakarta mb-1">Start your journey</h1>
          <p className="text-slate-400 text-sm mb-8">Free forever. No credit card needed.</p>

          <button
            onClick={handleGoogleSignup}
            className="w-full flex items-center justify-center gap-3 py-3 rounded-xl border border-white/10 hover:bg-white/5 transition-all text-sm mb-6"
          >
            <Chrome size={18} className="text-blue-400" />
            Sign up with Google
          </button>

          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs text-slate-500">or</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1.5">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Arjun Sharma"
                className="fin-input"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="fin-input"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min 8 characters"
                className="fin-input"
                minLength={8}
                required
              />
            </div>

            {error && (
              <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg py-2 px-3">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Creating account...' : 'Create Free Account'}
            </button>
          </form>

          <p className="text-center text-xs text-slate-600 mt-4">
            By signing up you agree to our terms. Not financial advice.
          </p>

          <p className="text-center text-sm text-slate-500 mt-4">
            Already have an account?{' '}
            <Link href="/login" className="text-indigo-400 hover:text-indigo-300">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  )
}
