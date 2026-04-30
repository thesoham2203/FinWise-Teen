'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertCircle, TrendingDown, X } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

interface Allocation {
  name: string
  percentage: number
  riskLevel: string
  monthlyAmount: number
}

interface StressTesterProps {
  allocation: Allocation[]
  currency: string
  onClose: () => void
}

const scenarios = [
  { id: 'covid', name: 'Covid 2020 Crash', drop: 25, period: '1 month' },
  { id: '2008', name: '2008 Financial Crisis', drop: 45, period: '12 months' },
  { id: 'dotcom', name: 'Dot-com Bubble', drop: 35, period: '18 months' },
  { id: 'moderate', name: 'Moderate Correction', drop: 10, period: '3 months' },
]

const riskMultipliers: Record<string, number> = {
  'Very Low': 0.05,
  'Low': 0.2,
  'Medium': 0.5,
  'Medium-High': 0.8,
  'High': 1.0,
  'Very High': 1.4,
}

export default function StressTester({ allocation, currency, onClose }: StressTesterProps) {
  const [selectedScenario, setSelectedScenario] = useState(scenarios[0])

  const calculateImpact = () => {
    let totalDrop = 0
    const details = allocation.map(a => {
      const multiplier = riskMultipliers[a.riskLevel] || 0.5
      const assetDropValue = (a.percentage / 100) * (selectedScenario.drop / 100) * multiplier
      totalDrop += assetDropValue
      return {
        name: a.name,
        dropPct: (selectedScenario.drop * multiplier).toFixed(1)
      }
    })

    return { totalDropPct: (totalDrop * 100).toFixed(1), details }
  }

  const impact = calculateImpact()

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="glass-card max-w-lg w-full p-6 relative shadow-2xl overflow-hidden"
      >
        <div className="absolute inset-0 z-0 opacity-10">
          <div className="h-full w-full bg-[radial-gradient(#ec4899_1px,transparent_1px)] [background-size:20px_20px]" />
        </div>

        <div className="relative z-10">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-rose-500/20 flex items-center justify-center">
                <AlertCircle className="text-rose-500" size={18} />
              </div>
              <h2 className="text-xl font-bold">What-If Stress Tester</h2>
            </div>
            <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
              <X size={20} />
            </button>
          </div>

          <div className="mb-6">
            <label className="text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-2 block">Choose Scenario</label>
            <div className="grid grid-cols-2 gap-2">
              {scenarios.map(s => (
                <button
                  key={s.id}
                  onClick={() => setSelectedScenario(s)}
                  className={`p-3 rounded-xl border text-left transition-all ${selectedScenario.id === s.id ? 'border-rose-500/50 bg-rose-500/10' : 'border-white/10 bg-white/5 hover:bg-white/10'}`}
                >
                  <div className="text-xs font-bold mb-1">{s.name}</div>
                  <div className="text-[10px] text-rose-400">-{s.drop}% Market Drop</div>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-rose-500/5 border border-rose-500/20 rounded-2xl p-5 mb-6 text-center">
            <div className="text-[10px] uppercase tracking-widest font-bold text-rose-400 mb-1">Your Portfolio Impact</div>
            <div className="text-4xl font-bold text-rose-500 glow-text mb-1">-{impact.totalDropPct}%</div>
            <p className="text-xs text-slate-400">Estimated value loss during {selectedScenario.name}</p>
          </div>

          <div className="space-y-2 mb-6 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
             {impact.details.map(d => (
               <div key={d.name} className="flex items-center justify-between text-[11px] p-2 bg-white/5 rounded-lg">
                 <span className="text-slate-400">{d.name}</span>
                 <span className="text-rose-400 font-mono">-{d.dropPct}%</span>
               </div>
             ))}
          </div>

          <div className="flex gap-3">
             <button onClick={onClose} className="flex-1 btn-ghost py-3 text-sm">Close Simulation</button>
             <button className="flex-1 btn-primary bg-rose-500 hover:bg-rose-600 shadow-rose-500/20 py-3 text-sm flex items-center justify-center gap-2">
               <TrendingDown size={16} />
               Optimize for Crashing
             </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
