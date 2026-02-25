'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp, Share2 } from 'lucide-react'
import { supabase } from '@/lib/supabase'
import { formatINR } from '@/lib/utils'
import AssetCard from '@/components/AssetCard'

const COLORS = ['#6366F1', '#10B981', '#F59E0B', '#EC4899', '#14B8A6', '#8B5CF6', '#F97316', '#06B6D4']

export default function SharedPlanPage({ params }: { params: { userId: string } }) {
  const [plan, setPlan] = useState<any>(null)
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const fetch_ = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/plan/${params.userId}/latest`)
        if (res.ok) setPlan(await res.json())
        const { data } = await supabase.from('user_profiles').select('full_name,occupation,risk_appetite,retirement_age').eq('user_id', params.userId).single()
        setProfile(data)
      } catch { /* empty */ }
      setLoading(false)
    }
    fetch_()
  }, [params.userId])

  const handleCopy = async () => {
    await navigator.clipboard.writeText(window.location.href)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  if (loading) return (
    <div className="min-h-screen bg-[#080B14] flex items-center justify-center">
      <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!plan) return (
    <div className="min-h-screen bg-[#080B14] flex items-center justify-center text-slate-400">
      Plan not found or private.
    </div>
  )

  return (
    <div className="min-h-screen bg-[#080B14] py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Brand */}
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
            <TrendingUp size={16} />
          </div>
          <span className="font-bold font-jakarta gradient-text">FinWise Teen</span>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-2xl font-bold font-jakarta">{profile?.full_name || 'A user'}&#39;s Investment Plan</h1>
              <p className="text-slate-400 text-sm mt-1">
                {profile?.occupation} · {profile?.risk_appetite} risk · Retire by {profile?.retirement_age}
              </p>
            </div>
            <button onClick={handleCopy} className="btn-ghost flex items-center gap-2 text-sm px-4 py-2">
              <Share2 size={14} /> {copied ? 'Copied!' : 'Copy Link'}
            </button>
          </div>

          {/* Summary metric */}
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="glass-card p-4 text-center">
              <div className="text-slate-400 text-sm mb-1">Monthly Investment</div>
              <div className="text-2xl font-bold gradient-text">{formatINR(plan.monthly_investment)}</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-slate-400 text-sm mb-1">Projected Corpus</div>
              <div className="text-2xl font-bold text-emerald-400">{formatINR(plan.retirement_projection?.projected_corpus || 0)}</div>
            </div>
          </div>

          {/* Pie */}
          <div className="glass-card p-6 mb-6">
            <h3 className="font-semibold mb-4">Portfolio Allocation</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={plan.allocation.map((a: any) => ({ name: a.name, value: a.percentage }))} cx="50%" cy="50%" innerRadius={55} outerRadius={85} dataKey="value" strokeWidth={0}>
                  {plan.allocation.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v: any) => [`${v}%`]} contentStyle={{ background: '#0D1120', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Assets */}
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {plan.allocation.map((a: any, i: number) => <AssetCard key={a.name} asset={a} color={COLORS[i % COLORS.length]} index={i} />)}
          </div>

          <div className="glass-card p-5 border border-indigo-500/20">
            <div className="text-sm font-semibold mb-2">✨ AI Reasoning</div>
            <p className="text-slate-300 text-sm leading-relaxed">{plan.reasoning}</p>
          </div>

          <div className="text-center mt-8">
            <p className="text-slate-500 text-sm mb-3">Want your own personalised plan?</p>
            <a href="/signup" className="btn-primary inline-flex">Get My Free Plan →</a>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
