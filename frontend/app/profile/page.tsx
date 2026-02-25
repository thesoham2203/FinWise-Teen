'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'
import { supabase } from '@/lib/supabase'
import DashboardNav from '@/components/DashboardNav'
import { Save, RefreshCw } from 'lucide-react'

export default function ProfilePage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [profile, setProfile] = useState<Record<string, any>>({})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!loading && !user) { router.push('/login'); return }
    if (user) {
      supabase.from('user_profiles').select('*').eq('user_id', user.id).single()
        .then(({ data }) => { if (data) setProfile(data) })
    }
  }, [user, loading, router])

  const set = (key: string, val: any) => setProfile(p => ({ ...p, [key]: val }))

  const handleSave = async () => {
    if (!user) return
    setSaving(true)
    await supabase.from('user_profiles').upsert({ ...profile, user_id: user.id }, { onConflict: 'user_id' })
    // Re-generate plan
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/plan/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...profile, user_id: user.id }),
    })
    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const currency = profile.preferred_currency || 'INR'
  const currSym = currency === 'USD' ? '$' : '₹'

  const fields = [
    { key: 'full_name', label: 'Full Name', type: 'text' },
    { key: 'age', label: 'Age', type: 'number' },
    { key: 'city', label: 'City', type: 'text' },
    { key: 'monthly_income', label: `Monthly Income (${currSym})`, type: 'number' },
    { key: 'monthly_expenses', label: `Monthly Expenses (${currSym})`, type: 'number' },
    { key: 'monthly_emis', label: `Monthly EMIs (${currSym})`, type: 'number' },
    { key: 'current_savings', label: `Current Savings (${currSym})`, type: 'number' },
    { key: 'dream_job', label: 'Dream Career', type: 'text' },
    { key: 'target_income_5yr', label: `Target Income in 5 Years (${currSym})`, type: 'number' },
    { key: 'retirement_age', label: 'Retirement Age Goal', type: 'number' },
    { key: 'target_corpus', label: `Target Retirement Corpus (${currSym})`, type: 'number' },
  ]

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div className="min-h-screen">
      <DashboardNav />
      <div className="pt-24 px-4 pb-12 max-w-2xl mx-auto">

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold font-jakarta mb-1">Edit Profile</h1>
          <p className="text-slate-400 text-sm mb-8">Update your details and regenerate your AI plan</p>

          <div className="glass-card p-6 space-y-4 mb-6">
            {fields.map(f => (
              <div key={f.key}>
                <label className="block text-sm text-slate-400 mb-1.5">{f.label}</label>
                <input
                  type={f.type}
                  value={profile[f.key] || ''}
                  onChange={e => set(f.key, e.target.value)}
                  className="fin-input"
                />
              </div>
            ))}

            <div>
              <label className="block text-sm text-slate-400 mb-2">Risk Appetite</label>
              <div className="grid grid-cols-3 gap-3">
                {['conservative', 'moderate', 'aggressive'].map(r => (
                  <button key={r} onClick={() => set('risk_appetite', r)}
                    className={`py-2.5 rounded-xl border text-sm font-medium capitalize transition-all ${profile.risk_appetite === r ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300' : 'border-white/10 text-slate-400 hover:border-white/20'}`}>
                    {r}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button onClick={handleSave} disabled={saving} className="btn-primary w-full flex items-center justify-center gap-2">
            {saving ? <><RefreshCw size={16} className="animate-spin" /> Saving & Regenerating...</> : saved ? '✅ Saved! Plan updated.' : <><Save size={16} /> Save & Regenerate Plan</>}
          </button>
        </motion.div>
      </div>
    </div>
  )
}
