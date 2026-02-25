'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { ChevronRight, ChevronLeft, Briefcase, Wallet, Star, Target, Sunrise } from 'lucide-react'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/components/providers/AuthProvider'

const steps = [
  { id: 1, title: 'About You', icon: Briefcase, desc: 'Let\'s get to know you' },
  { id: 2, title: 'Income & Expenses', icon: Wallet, desc: 'Your monthly numbers' },
  { id: 3, title: 'Ambitions', icon: Star, desc: 'Where you want to go' },
  { id: 4, title: 'Investment Style', icon: Target, desc: 'Your risk comfort zone' },
  { id: 5, title: 'Retirement Goal', icon: Sunrise, desc: 'The big picture' },
]

interface FormData {
  full_name: string
  age: string
  city: string
  occupation: string
  monthly_income: string
  monthly_expenses: string
  monthly_emis: string
  current_savings: string
  dream_job: string
  target_income_5yr: string
  risk_appetite: string
  investment_horizon_years: string
  retirement_age: string
  target_corpus: string
}

const initialData: FormData = {
  full_name: '', age: '', city: '', occupation: 'student',
  monthly_income: '', monthly_expenses: '', monthly_emis: '', current_savings: '',
  dream_job: '', target_income_5yr: '',
  risk_appetite: 'moderate', investment_horizon_years: '10',
  retirement_age: '50', target_corpus: '',
}

export default function OnboardPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [step, setStep] = useState(1)
  const [data, setData] = useState<FormData>(initialData)
  const [loading, setLoading] = useState(false)

  const set = (key: keyof FormData, val: string) => setData(prev => ({ ...prev, [key]: val }))

  const handleSubmit = async () => {
    if (!user) { router.push('/login'); return }
    setLoading(true)
    const payload = {
      user_id: user.id,
      full_name: data.full_name,
      age: parseInt(data.age),
      city: data.city,
      occupation: data.occupation,
      monthly_income: parseFloat(data.monthly_income),
      monthly_expenses: parseFloat(data.monthly_expenses),
      monthly_emis: parseFloat(data.monthly_emis || '0'),
      current_savings: parseFloat(data.current_savings || '0'),
      dream_job: data.dream_job,
      target_income_5yr: parseFloat(data.target_income_5yr || '0'),
      risk_appetite: data.risk_appetite,
      investment_horizon_years: parseInt(data.investment_horizon_years),
      retirement_age: parseInt(data.retirement_age),
      target_corpus: parseFloat(data.target_corpus || '0'),
    }
    try {
      await supabase.from('user_profiles').upsert(payload, { onConflict: 'user_id' })
      // Trigger plan generation
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/plan/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      router.push('/dashboard')
    } catch {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#080B14] flex items-center justify-center px-4 py-12 relative">
      <div className="hero-orb w-[500px] h-[500px] bg-indigo-600/10 -top-40 -left-40" />
      <div className="hero-orb w-[400px] h-[400px] bg-violet-600/8 bottom-0 right-0" />

      <div className="relative z-10 w-full max-w-2xl">
        {/* Progress steps */}
        <div className="flex items-center justify-between mb-8 px-2">
          {steps.map((s, i) => (
            <div key={s.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all
                  ${step === s.id ? 'step-active' : step > s.id ? 'step-done' : 'step-inactive'}`}>
                  {step > s.id ? '✓' : s.id}
                </div>
                <div className={`text-xs mt-1 hidden md:block font-medium ${step === s.id ? 'text-indigo-400' : 'text-slate-600'}`}>
                  {s.title}
                </div>
              </div>
              {i < steps.length - 1 && (
                <div className={`flex-1 h-px mx-2 w-8 md:w-16 transition-colors ${step > s.id ? 'bg-emerald-500/50' : 'bg-white/10'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.25 }}
            >
              {/* Step 1: About You */}
              {step === 1 && (
                <div>
                  <h2 className="text-2xl font-bold font-jakarta mb-1">Tell us about yourself</h2>
                  <p className="text-slate-400 text-sm mb-6">Basic info to personalise your plan</p>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">Full Name</label>
                      <input value={data.full_name} onChange={e => set('full_name', e.target.value)} placeholder="Arjun Sharma" className="fin-input" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-slate-400 mb-1.5">Age</label>
                        <input type="number" value={data.age} onChange={e => set('age', e.target.value)} placeholder="19" min="13" max="30" className="fin-input" />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-400 mb-1.5">City</label>
                        <input value={data.city} onChange={e => set('city', e.target.value)} placeholder="Mumbai" className="fin-input" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-2">I am currently a...</label>
                      <div className="grid grid-cols-3 gap-3">
                        {[
                          { val: 'student', label: '🎓 Student' },
                          { val: 'part_time', label: '⚡ Part-time' },
                          { val: 'full_time', label: '💼 Full-time' },
                        ].map(opt => (
                          <button
                            key={opt.val}
                            onClick={() => set('occupation', opt.val)}
                            className={`py-3 rounded-xl border text-sm font-medium transition-all ${
                              data.occupation === opt.val
                                ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300'
                                : 'border-white/10 text-slate-400 hover:border-white/20'
                            }`}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: Income & Expenses */}
              {step === 2 && (
                <div>
                  <h2 className="text-2xl font-bold font-jakarta mb-1">Your monthly finances</h2>
                  <p className="text-slate-400 text-sm mb-6">Be honest — this helps us calculate how much you can invest</p>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">Monthly Income / Stipend (₹)</label>
                      <input type="number" value={data.monthly_income} onChange={e => set('monthly_income', e.target.value)} placeholder="e.g. 25000" className="fin-input" />
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">Monthly Expenses (₹)</label>
                      <input type="number" value={data.monthly_expenses} onChange={e => set('monthly_expenses', e.target.value)} placeholder="e.g. 12000" className="fin-input" />
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">Monthly EMIs (₹) — 0 if none</label>
                      <input type="number" value={data.monthly_emis} onChange={e => set('monthly_emis', e.target.value)} placeholder="e.g. 5000" className="fin-input" />
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">Current Savings / FD / Investments (₹)</label>
                      <input type="number" value={data.current_savings} onChange={e => set('current_savings', e.target.value)} placeholder="e.g. 50000" className="fin-input" />
                    </div>
                    {/* Disposable income calculator */}
                    {data.monthly_income && data.monthly_expenses && (
                      <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
                        <div className="text-sm text-emerald-400 font-medium">
                          💰 Investable surplus: ₹{Math.max(0, parseFloat(data.monthly_income) - parseFloat(data.monthly_expenses) - parseFloat(data.monthly_emis || '0')).toLocaleString('en-IN')}/month
                        </div>
                        <div className="text-xs text-slate-400 mt-1">This is what we&apos;ll plan your investments around</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Step 3: Ambitions */}
              {step === 3 && (
                <div>
                  <h2 className="text-2xl font-bold font-jakarta mb-1">Your ambitions & goals</h2>
                  <p className="text-slate-400 text-sm mb-6">Dream big — your plan will be built around this</p>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">What&#39;s your dream job or career?</label>
                      <input value={data.dream_job} onChange={e => set('dream_job', e.target.value)} placeholder="e.g. Startup founder, Doctor, Software Engineer" className="fin-input" />
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">Target annual income in 5 years (₹)</label>
                      <input type="number" value={data.target_income_5yr} onChange={e => set('target_income_5yr', e.target.value)} placeholder="e.g. 1200000 (12 Lakhs)" className="fin-input" />
                    </div>
                    <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4">
                      <div className="text-sm text-indigo-300 font-medium mb-2">💡 What do you want to use your wealth for?</div>
                      <div className="grid grid-cols-2 gap-2">
                        {['Buy a house', 'Start a business', 'Travel the world', 'Support family', 'Early retirement', 'Education abroad'].map(goal => (
                          <label key={goal} className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                            <input type="checkbox" className="accent-indigo-500" />
                            {goal}
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 4: Investment Style */}
              {step === 4 && (
                <div>
                  <h2 className="text-2xl font-bold font-jakarta mb-1">Your investment style</h2>
                  <p className="text-slate-400 text-sm mb-6">This helps us balance growth vs safety in your plan</p>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm text-slate-400 mb-3">Risk Appetite</label>
                      <div className="space-y-3">
                        {[
                          { val: 'conservative', label: '🛡️ Conservative', desc: 'Prefer safety. FDs, bonds, and low-risk options.' },
                          { val: 'moderate', label: '⚖️ Moderate', desc: 'Balanced mix. Some stocks, some safe assets.' },
                          { val: 'aggressive', label: '🚀 Aggressive', desc: 'Max growth. Comfortable with market swings.' },
                        ].map(opt => (
                          <button
                            key={opt.val}
                            onClick={() => set('risk_appetite', opt.val)}
                            className={`w-full text-left p-4 rounded-xl border transition-all ${
                              data.risk_appetite === opt.val
                                ? 'border-indigo-500 bg-indigo-500/10'
                                : 'border-white/10 hover:border-white/20'
                            }`}
                          >
                            <div className="font-medium text-sm">{opt.label}</div>
                            <div className="text-xs text-slate-400 mt-1">{opt.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">
                        How long can you stay invested? — <span className="text-indigo-400 font-medium">{data.investment_horizon_years} years</span>
                      </label>
                      <input
                        type="range" min="1" max="40" value={data.investment_horizon_years}
                        onChange={e => set('investment_horizon_years', e.target.value)}
                        className="w-full accent-indigo-500"
                      />
                      <div className="flex justify-between text-xs text-slate-500 mt-1">
                        <span>1 year</span><span>40 years</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 5: Retirement Goal */}
              {step === 5 && (
                <div>
                  <h2 className="text-2xl font-bold font-jakarta mb-1">The big picture 🌅</h2>
                  <p className="text-slate-400 text-sm mb-6">When do you want to retire and how much do you need?</p>
                  <div className="space-y-5">
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">
                        Retire by age — <span className="text-indigo-400 font-medium">{data.retirement_age}</span>
                      </label>
                      <input
                        type="range" min="35" max="70" value={data.retirement_age}
                        onChange={e => set('retirement_age', e.target.value)}
                        className="w-full accent-indigo-500"
                      />
                      <div className="flex justify-between text-xs text-slate-500 mt-1">
                        <span>35 (very early)</span><span>70 (traditional)</span>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1.5">Target retirement corpus (₹) — optional</label>
                      <input type="number" value={data.target_corpus} onChange={e => set('target_corpus', e.target.value)} placeholder="e.g. 50000000 (5 Crore)" className="fin-input" />
                      <div className="text-xs text-slate-500 mt-1">Leave blank and AI will calculate what you need</div>
                    </div>

                    {data.age && data.retirement_age && (
                      <div className="bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/20 rounded-xl p-5">
                        <div className="text-sm font-semibold text-white mb-3">📊 Your snapshot</div>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-slate-400">Years to invest</div>
                            <div className="text-xl font-bold gradient-text">
                              {Math.max(0, parseInt(data.retirement_age) - parseInt(data.age))} yrs
                            </div>
                          </div>
                          <div>
                            <div className="text-slate-400">Monthly surplus</div>
                            <div className="text-xl font-bold text-emerald-400">
                              ₹{Math.max(0, parseFloat(data.monthly_income || '0') - parseFloat(data.monthly_expenses || '0') - parseFloat(data.monthly_emis || '0')).toLocaleString('en-IN')}
                            </div>
                          </div>
                          <div>
                            <div className="text-slate-400">Risk profile</div>
                            <div className="font-semibold text-amber-400 capitalize">{data.risk_appetite}</div>
                          </div>
                          <div>
                            <div className="text-slate-400">Dream career</div>
                            <div className="font-semibold text-indigo-300 truncate">{data.dream_job || 'Not set'}</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between mt-8">
            <button
              onClick={() => setStep(s => Math.max(1, s - 1))}
              disabled={step === 1}
              className="btn-ghost flex items-center gap-2 disabled:opacity-30"
            >
              <ChevronLeft size={16} /> Back
            </button>
            {step < 5 ? (
              <button
                onClick={() => setStep(s => Math.min(5, s + 1))}
                className="btn-primary flex items-center gap-2"
              >
                Continue <ChevronRight size={16} />
              </button>
            ) : (
              <motion.button
                onClick={handleSubmit}
                disabled={loading}
                whileHover={{ scale: 1.02 }}
                className="btn-primary flex items-center gap-2"
              >
                {loading ? '✨ Building your plan...' : '🚀 Generate My Plan'}
              </motion.button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
