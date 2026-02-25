'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, AreaChart, Area, XAxis, YAxis } from 'recharts'
import { TrendingUp, TrendingDown, RefreshCw, Share2, Target, Zap } from 'lucide-react'
import { useAuth } from '@/components/providers/AuthProvider'
import { supabase } from '@/lib/supabase'
import { formatINR } from '@/lib/utils'
import DashboardNav from '@/components/DashboardNav'
import AssetCard from '@/components/AssetCard'
import MarketPulse from '@/components/MarketPulse'

interface AllocationItem {
  name: string
  percentage: number
  monthlyAmount: number
  description: string
  instruments: string[]
  riskLevel: string
  color: string
  expectedReturn: string
}

interface Plan {
  allocation: AllocationItem[]
  monthly_investment: number
  reasoning: string
  retirement_projection: {
    years_to_retire: number
    projected_corpus: number
    monthly_needed: number
  }
}

const COLORS = ['#6366F1', '#10B981', '#F59E0B', '#EC4899', '#14B8A6', '#8B5CF6', '#F97316', '#06B6D4']

export default function DashboardPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [plan, setPlan] = useState<Plan | null>(null)
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null)
  const [loadingPlan, setLoadingPlan] = useState(true)
  const [regenerating, setRegenerating] = useState(false)
  const [shareLink, setShareLink] = useState('')

  const fetchPlan = useCallback(async () => {
    if (!user) return
    setLoadingPlan(true)
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/plan/${user.id}/latest`
      )
      if (res.ok) {
        const data = await res.json()
        setPlan(data)
      }
      const { data: profileData } = await supabase
        .from('user_profiles')
        .select('*')
        .eq('user_id', user.id)
        .single()
      setProfile(profileData)
    } catch {
      // handle error
    }
    setLoadingPlan(false)
  }, [user])

  useEffect(() => {
    if (!loading && !user) { router.push('/login'); return }
    if (user) fetchPlan()
  }, [user, loading, router, fetchPlan])

  const handleRegenerate = async () => {
    if (!user || !profile) return
    setRegenerating(true)
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/plan/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...profile, user_id: user.id }),
    })
    await fetchPlan()
    setRegenerating(false)
  }

  const handleShare = async () => {
    if (!user) return
    const link = `${window.location.origin}/plan/${user.id}`
    await navigator.clipboard.writeText(link)
    setShareLink(link)
    setTimeout(() => setShareLink(''), 3000)
  }

  if (loading || loadingPlan) {
    return (
      <div className="min-h-screen bg-[#080B14] flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"
          />
          <div className="text-slate-400">Loading your financial plan...</div>
        </div>
      </div>
    )
  }

  if (!plan) {
    return (
      <div className="min-h-screen bg-[#080B14] flex items-center justify-center px-4">
        <DashboardNav />
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">📋</div>
          <h2 className="text-2xl font-bold mb-2">No plan yet</h2>
          <p className="text-slate-400 mb-6">Complete your profile to get your personalised investment plan!</p>
          <button onClick={() => router.push('/onboard')} className="btn-primary">
            Set Up Profile
          </button>
        </div>
      </div>
    )
  }

  const pieData = plan.allocation.map(a => ({ name: a.name, value: a.percentage }))
  const projectionYears = plan.retirement_projection?.years_to_retire || 20
  const projectionData = Array.from({ length: Math.min(projectionYears, 30) }, (_, i) => ({
    year: `Y${i + 1}`,
    corpus: Math.round((plan.monthly_investment * 12 * (i + 1)) * Math.pow(1.12, i + 1)),
  }))

  return (
    <div className="min-h-screen bg-[#080B14]">
      <DashboardNav />
      <div className="pt-20 px-4 pb-12 max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8"
        >
          <div>
            <h1 className="text-2xl font-bold font-jakarta">
              Your Investment Plan 📊
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              AI-generated based on your financial profile · Updated just now
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleShare}
              className="btn-ghost flex items-center gap-2 text-sm px-4 py-2"
            >
              <Share2 size={15} />
              {shareLink ? '✅ Copied!' : 'Share Plan'}
            </button>
            <button
              onClick={handleRegenerate}
              disabled={regenerating}
              className="btn-primary flex items-center gap-2 text-sm px-4 py-2"
            >
              <RefreshCw size={15} className={regenerating ? 'animate-spin' : ''} />
              {regenerating ? 'Regenerating...' : 'Regenerate'}
            </button>
          </div>
        </motion.div>

        {/* Key metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            {
              label: 'Monthly Investment',
              value: formatINR(plan.monthly_investment),
              sub: 'Recommended SIP',
              icon: Zap,
              color: 'text-indigo-400',
            },
            {
              label: 'Projected Corpus',
              value: formatINR(plan.retirement_projection?.projected_corpus || 0),
              sub: `In ${projectionYears} years`,
              icon: Target,
              color: 'text-emerald-400',
            },
            {
              label: 'Years to Retire',
              value: `${projectionYears}`,
              sub: `Age ${(profile?.age as number || 20) + projectionYears}`,
              icon: TrendingUp,
              color: 'text-amber-400',
            },
            {
              label: 'Asset Classes',
              value: `${plan.allocation.length}`,
              sub: 'Diversified portfolio',
              icon: TrendingDown,
              color: 'text-violet-400',
            },
          ].map((m, i) => (
            <motion.div
              key={m.label}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-card p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs text-slate-500">{m.label}</div>
                <m.icon size={16} className={m.color} />
              </div>
              <div className={`text-2xl font-bold ${m.color}`}>{m.value}</div>
              <div className="text-xs text-slate-500 mt-1">{m.sub}</div>
            </motion.div>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Allocation pie */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6"
          >
            <h3 className="font-semibold mb-4">Portfolio Allocation</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {pieData.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v) => [`${v}%`]}
                  contentStyle={{ background: '#0D1120', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, color: '#F1F5F9' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 mt-2">
              {plan.allocation.slice(0, 6).map((a, i) => (
                <div key={a.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                    <span className="text-slate-300 text-xs">{a.name}</span>
                  </div>
                  <span className="font-semibold text-xs">{a.percentage}%</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Projection chart */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6 lg:col-span-2"
          >
            <h3 className="font-semibold mb-1">Wealth Growth Projection</h3>
            <p className="text-xs text-slate-500 mb-4">Assuming 12% annualised return (NIFTY 50 historical avg)</p>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={projectionData}>
                <defs>
                  <linearGradient id="corpusGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v) => formatINR(v)} tick={{ fontSize: 10 }} width={60} />
                <Tooltip
                  formatter={(v: unknown) => [formatINR(v as number), 'Projected Corpus']}
                  contentStyle={{ background: '#0D1120', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, color: '#F1F5F9' }}
                />
                <Area type="monotone" dataKey="corpus" stroke="#6366F1" fill="url(#corpusGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Asset class cards */}
        <h3 className="font-semibold mb-4 text-lg">Where to Put Your Money 💰</h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {plan.allocation.map((asset, i) => (
            <AssetCard key={asset.name} asset={asset} color={COLORS[i % COLORS.length]} index={i} />
          ))}
        </div>

        {/* Market Pulse */}
        <MarketPulse />

        {/* AI Reasoning */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="glass-card p-6 mt-6"
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-xs">✨</div>
            <h3 className="font-semibold">AI Reasoning</h3>
          </div>
          <p className="text-slate-300 text-sm leading-relaxed">{plan.reasoning}</p>
        </motion.div>
      </div>
    </div>
  )
}
