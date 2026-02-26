'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, AreaChart, Area, XAxis, YAxis } from 'recharts'
import { TrendingUp, TrendingDown, RefreshCw, Share2, Target, Zap, AlertCircle, X, Copy, Check, QrCode } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'

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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v2'










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
  const [showShareModal, setShowShareModal] = useState(false)
  const [copied, setCopied] = useState(false)





  const fetchPlan = useCallback(async () => {
    if (!user) return
    setLoadingPlan(true)
    try {
      const res = await fetch(`${API_BASE_URL}/plan/${user.id}/latest`)
      if (res.ok) {
        const data = await res.json()
        setPlan(data)
        // Cache plan in localStorage for the FinWise Genie chatbot context
        localStorage.setItem('finwise_plan', JSON.stringify(data))
        localStorage.setItem('finwise_user_id', user.id)
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
    await fetch(`${API_BASE_URL}/plan/generate`, {

      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...profile, user_id: user.id }),
    })

    await fetchPlan()
    setRegenerating(false)
  }

  const handleShare = () => {
    if (!user) return
    const link = `${window.location.origin}/plan/${user.id}`
    setShareLink(link)
    setShowShareModal(true)
    setCopied(false)
  }

  const handleCopyLink = async () => {
    await navigator.clipboard.writeText(shareLink)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
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
              <QrCode size={15} />
              Share Plan
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

        {/* ─── TETRIS BODY GRID ─────────────────────────────────────────── */}
        <div className="grid lg:grid-cols-12 gap-4 mb-4 items-start">

          {/* ── LEFT COLUMN (3/12): Fitness → Badges → Peer ── */}
          <div className="lg:col-span-3 space-y-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="glass-card p-5">
              <FinancialFitnessScore
                allocation={plan.allocation}
                runwayMonths={parseFloat(runwayMonths.toFixed(1))}
                riskAppetite={profile?.risk_appetite as string || 'moderate'}
                monthlyInvestment={plan.monthly_investment}
                monthlyIncome={(profile?.monthly_income as number) || 0}
              />
            </motion.div>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }} className="glass-card p-5">
              <AchievementBadges
                allocation={plan.allocation}
                runwayMonths={runwayMonths}
                horizon={(profile?.investment_horizon_years as number) || 10}
              />
            </motion.div>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.18 }} className="glass-card p-5">
              <PeerBenchmarking
                userDiversification={plan.allocation.length}
                userCity={profile?.city as string || 'India'}
                userAge={profile?.age as number || 20}
              />
            </motion.div>
          </div>

          {/* ── CENTER COLUMN (6/12): Projection + Pie/Sliders ── */}
          <div className="lg:col-span-6 space-y-4">
            {/* Wealth Projection — full center width */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-card p-6">
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
              <ResponsiveContainer width="100%" height={200}>
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
              <div className="mt-3 p-3 bg-white/5 rounded-xl border border-white/5 flex items-center justify-between">
                <span className="text-[10px] text-slate-400">Current Yield:</span>
                <span className="text-[10px] font-bold text-indigo-400">{(weightedReturn * 100).toFixed(1)}% Pa</span>
              </div>
            </motion.div>

            {/* Portfolio Pie + Sliders — side by side below projection */}
            <div className="grid grid-cols-2 gap-4">
              {/* Mini Pie */}
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="glass-card p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-sm">Portfolio Mix</h3>
                  <button onClick={() => setShowStressTester(true)} className="text-[9px] uppercase font-bold text-rose-400 hover:text-rose-300 flex items-center gap-1">
                    <AlertCircle size={10} /> Stress Test
                  </button>
                </div>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-20 h-20 shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={pieData} cx="50%" cy="50%" innerRadius={28} outerRadius={38} dataKey="value" strokeWidth={0}>
                          {pieData.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex-1 space-y-1 min-w-0">
                    {currentAllocation.slice(0, 4).map((a) => (
                      <div key={a.name} className="flex items-center justify-between text-[9px]">
                        <span className="text-slate-500 truncate mr-1">{a.name}</span>
                        <span className="font-bold text-slate-300 shrink-0">{a.percentage}%</span>
                      </div>
                    ))}
                    {currentAllocation.length > 4 && (
                      <div className="text-[8px] text-indigo-400 font-bold">+ {currentAllocation.length - 4} More</div>
                    )}
                  </div>
                </div>
              </motion.div>

              {/* Tweak Sliders */}
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }} className="glass-card p-5">
                <h3 className="font-semibold text-sm mb-3">Tweak Allocation</h3>
                <TweakSliders
                  initialAllocation={plan.allocation}
                  onUpdate={(newAlloc: any) => setManualAllocation(newAlloc)}
                />
              </motion.div>
            </div>
          </div>

          {/* ── RIGHT COLUMN (3/12): News + Learning ── */}
          <div className="lg:col-span-3 space-y-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.16 }} className="glass-card p-5">
              <GlassyNewsFeed />
            </motion.div>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.22 }} className="glass-card p-5">
              <LearningQuest />
            </motion.div>
          </div>
        </div>

        {/* ─── ASSET CARDS — 3 columns, full width ─────────────────────── */}
        <div className="mb-4">
          <h3 className="font-semibold mb-3 text-base flex items-center gap-2">
            <span>Where to Put Your Money</span>
            <span>💰</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {plan.allocation.map((asset, i) => (
              <AssetCard key={asset.name} asset={asset} color={COLORS[i % COLORS.length]} index={i} currency={currency} />
            ))}
          </div>
        </div>

        {/* ─── MARKET PULSE — full width ───────────────────────────────── */}
        <div className="mb-4">
          <MarketPulse currency={currency} />
        </div>

        {/* ─── AI REASONING — full width ───────────────────────────────── */}
        <GlowCard className="p-6">
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
        {showShareModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowShareModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 rounded-3xl max-w-sm w-full mx-4 text-center relative"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setShowShareModal(false)}
                className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-colors"
              >
                <X size={18} />
              </button>

              <div className="mb-6">
                <div className="w-12 h-12 mx-auto rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 mb-3">
                  <QrCode className="text-indigo-400" size={24} />
                </div>
                <h3 className="text-lg font-bold font-jakarta">Share Your Plan</h3>
                <p className="text-xs text-slate-500 mt-1">Scan this QR or copy the link below</p>
              </div>

              {/* QR Code */}
              <div className="bg-white p-4 rounded-2xl inline-block mb-6">
                <QRCodeSVG
                  value={shareLink}
                  size={180}
                  bgColor="#FFFFFF"
                  fgColor="#1E1B4B"
                  level="H"
                  includeMargin={false}
                />
              </div>

              {/* Copy Link */}
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl p-3">
                <div className="flex-1 text-xs text-slate-400 truncate font-mono text-left">
                  {shareLink}
                </div>
                <button
                  onClick={handleCopyLink}
                  className={`shrink-0 px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
                    copied 
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/30'
                  }`}
                >
                  {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

