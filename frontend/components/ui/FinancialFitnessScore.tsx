'use client'

import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Shield, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react'

interface Allocation {
  name: string
  percentage: number
  riskLevel: string
}

interface FinancialFitnessScoreProps {
  allocation: Allocation[]
  runwayMonths: number
  riskAppetite: string
  monthlyInvestment: number
  monthlyIncome: number
}

export default function FinancialFitnessScore({ 
  allocation, 
  runwayMonths, 
  riskAppetite,
  monthlyInvestment,
  monthlyIncome
}: FinancialFitnessScoreProps) {
  
  const scoreData = useMemo(() => {
    let score = 0
    const breakdowns = []

    // 1. Diversification (Max 40)
    const uniqueClasses = allocation.length
    const divScore = Math.min(40, uniqueClasses * 8)
    score += divScore
    breakdowns.push({ label: 'Diversification', score: divScore, max: 40, icon: TrendingUp })

    // 2. Emergency Runway (Max 25)
    const runScore = Math.min(25, runwayMonths * 4)
    score += runScore
    breakdowns.push({ label: 'Safety Net', score: runScore, max: 25, icon: Shield })

    // 3. Investment Discipline (Max 20)
    const savingsRate = (monthlyInvestment / Math.max(1, monthlyIncome)) * 100
    const disciplineScore = Math.min(20, savingsRate / 1.5)
    score += disciplineScore
    breakdowns.push({ label: 'Discipline', score: Math.round(disciplineScore), max: 20, icon: CheckCircle2 })

    // 4. Alignment (Max 15)
    // Simplified checks
    const hasHighRisk = allocation.some(a => a.riskLevel === 'High' || a.riskLevel === 'Very High')
    let alignmentScore = 15
    if (riskAppetite === 'conservative' && hasHighRisk) alignmentScore = 5
    score += alignmentScore
    breakdowns.push({ label: 'Risk Alignment', score: alignmentScore, max: 15, icon: AlertTriangle })

    return { total: Math.round(score), breakdowns }
  }, [allocation, runwayMonths, riskAppetite, monthlyInvestment, monthlyIncome])

  const getColor = (s: number) => {
    if (s > 80) return 'text-emerald-400'
    if (s > 60) return 'text-amber-400'
    return 'text-rose-400'
  }

  const getStrokeColor = (s: number) => {
    if (s > 80) return '#34d399'
    if (s > 60) return '#fbbf24'
    return '#fb7185'
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-sm">Financial Fitness</h3>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full bg-white/5 border border-white/10 ${getColor(scoreData.total)}`}>
          {scoreData.total > 80 ? 'EXCELLENT' : scoreData.total > 60 ? 'HEALTHY' : 'NEEDS ACTION'}
        </span>
      </div>

      <div className="flex items-center gap-8 mb-8">
        <div className="relative w-24 h-24 flex-shrink-0">
          <svg className="w-full h-full -rotate-90 transform">
            <circle
              cx="48"
              cy="48"
              r="40"
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="8"
              fill="transparent"
            />
            <motion.circle
              cx="48"
              cy="48"
              r="40"
              stroke={getStrokeColor(scoreData.total)}
              strokeWidth="8"
              strokeDasharray={251.2}
              initial={{ strokeDashoffset: 251.2 }}
              animate={{ strokeDashoffset: 251.2 - (251.2 * scoreData.total) / 100 }}
              transition={{ duration: 1.5, ease: "easeOut" }}
              strokeLinecap="round"
              fill="transparent"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center flex-col">
            <span className={`text-2xl font-bold font-mono ${getColor(scoreData.total)}`}>{scoreData.total}</span>
            <span className="text-[8px] text-slate-500 uppercase tracking-widest font-bold">SCORE</span>
          </div>
        </div>

        <div className="flex-1 space-y-3">
          {scoreData.breakdowns.map((b) => (
            <div key={b.label}>
              <div className="flex items-center justify-between text-[10px] mb-1">
                <span className="text-slate-400 flex items-center gap-1">
                  <b.icon size={10} /> {b.label}
                </span>
                <span className="font-bold text-slate-300">{b.score}/{b.max}</span>
              </div>
              <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${(b.score / b.max) * 100}%` }}
                  transition={{ duration: 1, delay: 0.5 }}
                  className="h-full bg-indigo-500/50" 
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="text-[10px] text-slate-500 leading-relaxed italic mt-auto">
        "Your score is based on Indian personal finance best practices for young adults."
      </p>
    </div>
  )
}
