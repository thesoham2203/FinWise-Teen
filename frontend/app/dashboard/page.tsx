'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, AreaChart, Area, XAxis, YAxis } from 'recharts'
import { TrendingUp, TrendingDown, RefreshCw, Share2, Target, Zap, AlertCircle } from 'lucide-react'

import { useAuth } from '@/components/providers/AuthProvider'
import { supabase } from '@/lib/supabase'
import { formatCurrency } from '@/lib/utils'
import DashboardNav from '@/components/DashboardNav'
import AssetCard from '@/components/AssetCard'
import MarketPulse from '@/components/MarketPulse'
import GlowCard from '@/components/ui/GlowCard'
import BrandLogo from '@/components/BrandLogo'
import BlueprintGrid from '@/components/ui/BlueprintGrid'
import StressTester from '@/components/ui/StressTester'
import FinancialFitnessScore from '@/components/ui/FinancialFitnessScore'
import AchievementBadges from '@/components/ui/AchievementBadges'
import PeerBenchmarking from '@/components/ui/PeerBenchmarking'
import LearningQuest from '@/components/ui/LearningQuest'
import TweakSliders from '@/components/ui/TweakSliders'
import GlassyNewsFeed from '@/components/ui/GlassyNewsFeed'









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
  const [applyInflation, setApplyInflation] = useState(false)
  const [applyTax, setApplyTax] = useState(false)
  const [showStressTester, setShowStressTester] = useState(false)
  const [manualAllocation, setManualAllocation] = useState<AllocationItem[] | null>(null)





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

  const currentAllocation = manualAllocation || plan.allocation || []
  const pieData = currentAllocation.map(a => ({ name: a.name, value: a.percentage }))
  const projectionYears = plan.retirement_projection?.years_to_retire || 20

  // Calculate Weighted Return
  const getWeightedReturn = () => {
    if (!currentAllocation.length) return 0.12
    const total = currentAllocation.reduce((acc, a) => {
      const rateStr = a.expectedReturn || '12%'
      const rate = parseFloat(rateStr.replace('%', '')) / 100
      return acc + (rate * (a.percentage / 100))
    }, 0)
    return total
  }

  const weightedReturn = getWeightedReturn()

  // Refined calculation: FV of Annuity
  // r = annual rate, i = years, P = monthly investment
  const calculateCorpus = (years: number, nominalRate = weightedReturn, inflationRate = 0.06) => {
    const monthlyRate = nominalRate / 12
    const months = years * 12
    const p = plan.monthly_investment
    const totalInvested = p * months
    
    // Future Value of Monthly SIP (Nominal)
    const nominalFV = p * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate)
    
    let finalValue = nominalFV

    // Apply 12.5% LTCG Tax on gains (exceeding 1.25L exemption)
    if (applyTax) {
      const gains = Math.max(0, nominalFV - totalInvested)
      const taxableGains = Math.max(0, gains - 125000)
      const tax = taxableGains * 0.125
      finalValue = nominalFV - tax
    }
    
    if (!applyInflation) return Math.round(finalValue)
    
    // Discount for inflation to get "Today's Purchasing Power"
    return Math.round(finalValue / Math.pow(1 + inflationRate, years))
  }

  const projectionData = Array.from({ length: Math.min(projectionYears, 30) }, (_, i) => ({
    year: `Y${i + 1}`,
    corpus: calculateCorpus(i + 1),
  }))



  const currency = (profile?.preferred_currency as string) || 'INR'
  
  // Emergency Fund Runway calculation
  const emergencyFundAmount = plan.allocation.find(a => a.name.toLowerCase().includes('emergency'))?.monthlyAmount || 0
  const monthlyExpenses = (profile?.monthly_expenses as number) || 1
  const runwayMonths = (emergencyFundAmount * 12) / monthlyExpenses

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="absolute inset-0 z-0">
        <BlueprintGrid />
      </div>
      <DashboardNav />
      <div className="pt-24 px-4 pb-12 max-w-7xl mx-auto relative z-10">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-10"
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
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">

          {[
            {
              label: 'Monthly Investment',
              value: formatCurrency(plan.monthly_investment, currency),
              sub: 'Recommended SIP',
              icon: Zap,
              color: 'text-indigo-400',
            },
            {
              label: 'Projected Corpus',
              value: formatCurrency(projectionData[projectionData.length - 1]?.corpus || 0, currency),
              sub: `${applyInflation || applyTax ? 'Adjusted' : 'Nominal'} (30 Year)`,
              icon: Target,
              color: 'text-emerald-400',
            },
            {
              label: 'Survival Runway',
              value: `${((plan.allocation.find(a => a.name.toLowerCase().includes('emergency'))?.monthlyAmount || 0) * 12 / ((profile?.monthly_expenses as number) || 1)).toFixed(1)} Mo`,
              sub: 'Emergency safety net',
              icon: RefreshCw,
              color: 'text-rose-400',
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
            <GlowCard
              key={m.label}
              className="p-5 group"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="text-[10px] uppercase tracking-widest font-bold text-slate-500">{m.label}</div>
                <m.icon size={16} className={`${m.color} glow-primary`} />
              </div>
              <div className={`text-2xl font-bold tracking-tight ${m.color} glow-text`}>{m.value}</div>
              <div className="text-[10px] font-medium text-slate-400 mt-2 flex items-center gap-1">
                <span className="w-1 h-1 rounded-full bg-slate-600" /> {m.sub}
              </div>
            </GlowCard>


          ))}
        </div>

        <div className="grid lg:grid-cols-6 gap-6 mb-8">
          {/* Sidebar Left: Health & Social */}
          <div className="lg:col-span-1 space-y-6">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="glass-card p-5"
            >
              <FinancialFitnessScore 
                allocation={plan.allocation}
                runwayMonths={parseFloat(runwayMonths.toFixed(1))}
                riskAppetite={profile?.risk_appetite as string || 'moderate'}
                monthlyInvestment={plan.monthly_investment}
                monthlyIncome={(profile?.monthly_income as number) || 0}
              />
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.15 }}
              className="glass-card p-5"
            >
               <AchievementBadges 
                 allocation={plan.allocation}
                 runwayMonths={runwayMonths}
                 horizon={(profile?.investment_horizon_years as number) || 10}
               />
            </motion.div>
          </div>

          {/* Sidebar Right: Market & Benchmarking */}
          <div className="lg:col-span-1 space-y-6">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.16 }}
              className="glass-card p-5"
            >
               <GlassyNewsFeed />
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.18 }}
              className="glass-card p-5"
            >
               <PeerBenchmarking 
                 userDiversification={plan.allocation.length}
                 userCity={profile?.city as string || 'India'}
                 userAge={profile?.age as number || 20}
               />
            </motion.div>
          </div>

          {/* Main: Weightage & Projection */}
          <div className="lg:col-span-4 grid grid-cols-1 md:grid-cols-2 gap-6">
             {/* Projection chart */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="glass-card p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-sm mb-1">Wealth Projection</h3>
                  <p className="text-[10px] text-slate-500">Real-time simulation</p>
                </div>
                <div className="flex items-center gap-1 bg-white/5 p-1 rounded-lg border border-white/5">
                  <button onClick={() => { setApplyInflation(false); setApplyTax(false); }} className={`px-2 py-1 text-[8px] uppercase font-bold rounded ${!applyInflation && !applyTax ? 'bg-indigo-500 text-white' : 'text-slate-500'}`}>Nominal</button>
                  <button onClick={() => setApplyInflation(!applyInflation)} className={`px-2 py-1 text-[8px] uppercase font-bold rounded ${applyInflation ? 'bg-indigo-500 text-white' : 'text-slate-500'}`}>Inflation</button>
                  <button onClick={() => setApplyTax(!applyTax)} className={`px-2 py-1 text-[8px] uppercase font-bold rounded ${applyTax ? 'bg-indigo-500 text-white' : 'text-slate-500'}`}>Tax</button>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={projectionData}>
                  <defs>
                    <linearGradient id="corpusGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                  <YAxis tickFormatter={(v) => formatCurrency(v, currency)} tick={{ fontSize: 9 }} width={50} />
                  <Tooltip
                    formatter={(v: unknown) => [formatCurrency(v as number, currency), 'Corpus']}
                    contentStyle={{ background: '#0D1120', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, color: '#F1F5F9' }}
                  />
                  <Area type="monotone" dataKey="corpus" stroke="#6366F1" fill="url(#corpusGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
              
              <div className="mt-4 p-3 bg-white/5 rounded-xl border border-white/5 flex items-center justify-between">
                 <span className="text-[10px] text-slate-400">Current Yield:</span>
                 <span className="text-[10px] font-bold text-indigo-400">{(weightedReturn * 100).toFixed(1)}% Pa</span>
              </div>
            </motion.div>

            {/* Allocation pie & Sliders */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="glass-card p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm">Portfolio Logic</h3>
                <button onClick={() => setShowStressTester(true)} className="text-[9px] uppercase font-bold text-rose-400 hover:text-rose-300 flex items-center gap-1">
                  <AlertCircle size={10} /> Stress Test
                </button>
              </div>

              <div className="flex items-center gap-4 mb-6">
                <div className="w-24 h-24">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={35} outerRadius={45} dataKey="value" strokeWidth={0}>
                        {pieData.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex-1 space-y-1">
                   {currentAllocation.slice(0, 3).map((a, i) => (
                     <div key={a.name} className="flex items-center justify-between text-[9px]">
                        <span className="text-slate-500">{a.name}</span>
                        <span className="font-bold text-slate-300">{a.percentage}%</span>
                     </div>
                   ))}
                   <div className="text-[8px] text-indigo-400 mt-1 font-bold">+ {currentAllocation.length - 3} More</div>
                </div>
              </div>

              <div className="border-t border-white/5 pt-4">
                 <TweakSliders 
                   initialAllocation={plan.allocation} 
                   onUpdate={(newAlloc: any) => setManualAllocation(newAlloc)} 
                 />
              </div>
            </motion.div>
          </div>
        </div>


        {/* Asset breakdown and Learning Quest */}
        <div className="grid lg:grid-cols-4 gap-6 mb-10">
          <div className="lg:col-span-3">
            <h3 className="font-semibold mb-4 text-lg">Where to Put Your Money 💰</h3>
            <div className="grid md:grid-cols-2 gap-4">
              {plan.allocation.map((asset, i) => (
                <AssetCard key={asset.name} asset={asset} color={COLORS[i % COLORS.length]} index={i} currency={currency} />
              ))}
            </div>
          </div>
          <div className="lg:col-span-1">
            <LearningQuest />
          </div>
        </div>


        {/* Market Pulse */}
        <MarketPulse currency={currency} />


        {/* AI Reasoning */}
        <GlowCard className="p-6 mt-6">
          <div className="flex items-center gap-2 mb-3">
            <BrandLogo size={24} />
            <h3 className="font-semibold">AI Reasoning</h3>
          </div>
          <p className="text-slate-300 text-sm leading-relaxed">{plan.reasoning}</p>
        </GlowCard>

      </div>
      {/* Modals */}
      <AnimatePresence>
        {showStressTester && (
          <StressTester 
            allocation={plan.allocation} 
            currency={currency} 
            onClose={() => setShowStressTester(false)} 
          />
        )}
      </AnimatePresence>
    </div>
  )
}

