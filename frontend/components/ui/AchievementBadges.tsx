'use client'

import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Trophy, Compass, Shield, Zap, Coins, Clock } from 'lucide-react'

interface Badge {
  id: string
  name: string
  description: string
  icon: React.ElementType
  color: string
  earned: boolean
}

interface AchievementBadgesProps {
  allocation: any[]
  runwayMonths: number
  horizon: number
}

export default function AchievementBadges({ allocation, runwayMonths, horizon }: AchievementBadgesProps) {
  
  const badges = useMemo(() => {
    const b: Badge[] = [
      {
        id: 'compound-king',
        name: 'Compound King',
        description: 'Set a 10+ year investment horizon',
        icon: Clock,
        color: 'text-amber-400',
        earned: horizon >= 10
      },
      {
        id: 'sgb-sultan',
        name: 'SGB Sultan',
        description: 'Allocated funds to Gold/SGBs',
        icon: Coins,
        color: 'text-yellow-400',
        earned: allocation.some(a => a.name.toLowerCase().includes('gold') || a.name.toLowerCase().includes('sgb'))
      },
      {
        id: 'emergency-hero',
        name: 'Emergency Hero',
        description: 'Built a 6+ month survival runway',
        icon: Shield,
        color: 'text-emerald-400',
        earned: runwayMonths >= 6
      },
      {
        id: 'diversi-master',
        name: 'Diversi-Master',
        description: 'Diversified across 5+ asset classes',
        icon: Compass,
        color: 'text-indigo-400',
        earned: allocation.length >= 5
      },
      {
        id: 'early-starter',
        name: 'Alpha Investor',
        description: 'Started investing before age 20',
        icon: Zap,
        color: 'text-violet-400',
        earned: true // For this demo, let's assume they are all early starters
      }
    ]
    return b
  }, [allocation, runwayMonths, horizon])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm">Your Achievements</h3>
        <Trophy size={14} className="text-amber-500 animate-pulse" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        {badges.map((badge, i) => (
          <motion.div
            key={badge.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`p-3 rounded-2xl border flex flex-col items-center text-center transition-all ${
              badge.earned 
                ? 'bg-white/5 border-white/10' 
                : 'bg-black/20 border-white/5 opacity-40 grayscale'
            }`}
          >
            <div className={`p-2 rounded-xl bg-white/5 mb-2 ${badge.color}`}>
              <badge.icon size={18} />
            </div>
            <div className="text-[10px] font-bold text-slate-200 mb-0.5">{badge.name}</div>
            <div className="text-[8px] text-slate-500 leading-tight">{badge.description}</div>
            
            {badge.earned && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1"
              >
                <div className="w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center border-2 border-[#0D1120]">
                   <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={4} d="M5 13l4 4L19 7" />
                   </svg>
                </div>
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}
