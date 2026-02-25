'use client'

import { motion } from 'framer-motion'
import { ExternalLink, TrendingUp } from 'lucide-react'

interface Asset {
  name: string
  percentage: number
  monthlyAmount: number
  description: string
  instruments: string[]
  riskLevel: string
  expectedReturn: string
}

interface AssetCardProps {
  asset: Asset
  color: string
  index: number
  currency?: string
}


const riskColors: Record<string, string> = {
  'Very Low': 'text-emerald-400',
  'Low': 'text-green-400',
  'Medium': 'text-amber-400',
  'Medium-High': 'text-orange-400',
  'High': 'text-red-400',
  'Very High': 'text-rose-400',
}

import { formatCurrency } from '@/lib/utils'

export default function AssetCard({ asset, color, index, currency = 'INR' }: AssetCardProps) {

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className="glass-card p-5 hover:scale-[1.01] transition-transform"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}22` }}>
            <TrendingUp size={18} style={{ color }} />
          </div>
          <div>
            <div className="font-semibold text-sm">{asset.name}</div>
            <div className={`text-xs ${riskColors[asset.riskLevel] || 'text-slate-400'}`}>
              Risk: {asset.riskLevel}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xl font-bold" style={{ color }}>{asset.percentage}%</div>
          <div className="text-xs text-slate-500">of portfolio</div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-white/5 rounded-full mb-3 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${asset.percentage}%` }}
          transition={{ delay: index * 0.06 + 0.3, duration: 0.6 }}
          className="h-full rounded-full"
          style={{ background: color }}
        />
      </div>

      {/* Monthly amount */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-slate-500">Monthly Allocation</span>
        <span className="text-sm font-bold text-white">
          {formatCurrency(asset.monthlyAmount, currency)}
        </span>
      </div>


      {/* Return */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs text-slate-500">Expected Return</span>
        <span className="text-xs font-medium text-emerald-400">{asset.expectedReturn} p.a.</span>
      </div>

      <p className="text-xs text-slate-400 mb-3 leading-relaxed">{asset.description}</p>

      {/* Instruments */}
      {asset.instruments && asset.instruments.length > 0 && (
        <div className="border-t border-white/5 pt-3">
          <div className="text-xs text-slate-500 mb-2">Suggested instruments:</div>
          <div className="flex flex-wrap gap-1.5">
            {asset.instruments.slice(0, 3).map(inst => (
              <span key={inst} className="text-xs bg-white/5 rounded-md px-2 py-0.5 text-slate-300 flex items-center gap-1">
                {inst}
                <ExternalLink size={9} className="text-slate-500" />
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}
