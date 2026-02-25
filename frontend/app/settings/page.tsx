'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'
import { supabase } from '@/lib/supabase'
import DashboardNav from '@/components/DashboardNav'
import { 
  Settings as SettingsIcon, 
  Shield, 
  Sparkles, 
  Globe, 
  Trash2, 
  Check, 
  ArrowRight,
  LogOut
} from 'lucide-react'

export default function SettingsPage() {
  const { user, loading, signOut } = useAuth()
  const router = useRouter()
  const [profile, setProfile] = useState<any>({})
  const [latestPlan, setLatestPlan] = useState<any>(null)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user) { router.push('/login'); return }
    if (user) {
      // Fetch profile
      supabase.from('user_profiles').select('*').eq('user_id', user.id).single()
        .then(({ data }) => { if (data) setProfile(data) })
      
      // Fetch latest plan for privacy toggle
      supabase.from('investment_plans').select('*').eq('user_id', user.id).order('generated_at', { ascending: false }).limit(1).single()
        .then(({ data }) => { if (data) setLatestPlan(data) })
    }
  }, [user, loading, router])

  const showSuccess = (msg: string) => {
    setSuccess(msg)
    setTimeout(() => setSuccess(null), 3000)
  }

  const updatePreference = async (key: string, value: any) => {
    setSaving(true)
    const { error } = await supabase
      .from('user_profiles')
      .update({ [key]: value })
      .eq('user_id', user?.id)
    
    if (!error) {
      setProfile({ ...profile, [key]: value })
      showSuccess('Preference updated')
    }
    setSaving(false)
  }

  const togglePublic = async () => {
    if (!latestPlan) return
    const newVal = !latestPlan.is_public
    const { error } = await supabase
      .from('investment_plans')
      .update({ is_public: newVal })
      .eq('id', latestPlan.id)
    
    if (!error) {
      setLatestPlan({ ...latestPlan, is_public: newVal })
      showSuccess(newVal ? 'Plan is now public' : 'Plan is now private')
    }
  }

  const handleDeleteData = async () => {
    if (confirm('Are you sure? This will permanently delete your profile and all investment plans. This cannot be undone.')) {
      await supabase.from('investment_plans').delete().eq('user_id', user?.id)
      await supabase.from('user_profiles').delete().eq('user_id', user?.id)
      await signOut()
      router.push('/')
    }
  }

  if (loading) return (
    <div className="min-h-screen bg-[#080B14] flex items-center justify-center">
      <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="min-h-screen bg-[#080B14]">
      <DashboardNav />
      
      <main className="pt-24 pb-20 px-4 max-w-3xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
              <SettingsIcon className="text-indigo-400" size={20} />
            </div>
            <h1 className="text-3xl font-bold font-jakarta">Settings</h1>
          </div>
          <p className="text-slate-400">Manage your preferences, privacy, and account</p>
        </motion.div>

        <AnimatePresence>
          {success && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6"
            >
              <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-3 rounded-xl flex items-center gap-2 text-sm">
                <Check size={16} /> {success}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="space-y-6">
          {/* AI Personality */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <Sparkles className="text-indigo-400" size={18} />
              <h2 className="font-semibold">AI Advisor Personality</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { id: 'chill', label: 'Chill', desc: 'Friendly, approachable, teen-speak' },
                { id: 'moderate', label: 'Balanced', desc: 'Practical and helpful advice' },
                { id: 'pro', label: 'Strict Pro', desc: 'Direct, data-driven, no-nonsense' }
              ].map((type) => (
                <button
                  key={type.id}
                  onClick={() => updatePreference('ai_advisor_type', type.id)}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    profile.ai_advisor_type === type.id 
                    ? 'border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500/50' 
                    : 'border-white/5 bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <div className="font-bold text-sm mb-1">{type.label}</div>
                  <div className="text-xs text-slate-500">{type.desc}</div>
                </button>
              ))}
            </div>
          </section>

          {/* Regional Settings */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <Globe className="text-indigo-400" size={18} />
              <h2 className="font-semibold">Regional Preferences</h2>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
              <div>
                <div className="font-bold text-sm">Primary Currency</div>
                <div className="text-xs text-slate-500">How your investment amounts are displayed</div>
              </div>
              <div className="flex bg-black/20 p-1 rounded-lg border border-white/5">
                {['INR', 'USD'].map(curr => (
                  <button
                    key={curr}
                    onClick={() => updatePreference('preferred_currency', curr)}
                    className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${
                      profile.preferred_currency === curr 
                      ? 'bg-indigo-500 text-white shadow-lg' 
                      : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {curr}
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Privacy */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <Shield className="text-indigo-400" size={18} />
              <h2 className="font-semibold">Privacy & Sharing</h2>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
              <div>
                <div className="font-bold text-sm">Shareable Plan</div>
                <div className="text-xs text-slate-500">Anyone with the link can view your latest plan</div>
              </div>
              <button 
                onClick={togglePublic}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  latestPlan?.is_public ? 'bg-indigo-500' : 'bg-slate-700'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  latestPlan?.is_public ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            {latestPlan?.is_public && (
              <motion.div 
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-3 bg-indigo-500/5 rounded-lg border border-indigo-500/10 flex items-center justify-between gap-4"
              >
                <div className="text-xs text-indigo-300 truncate font-mono">
                  {typeof window !== 'undefined' ? `${window.location.origin}/plan/${user?.id}` : ''}
                </div>
                <button 
                  onClick={() => router.push(`/plan/${user?.id}`)}
                  className="text-xs text-white font-bold flex items-center gap-1 hover:underline whitespace-nowrap"
                >
                  View <ArrowRight size={12} />
                </button>
              </motion.div>
            )}
          </section>

          {/* Account */}
          <section className="glass-card p-6 border-red-500/10">
            <div className="flex items-center gap-3 mb-6">
              <Trash2 className="text-red-400" size={18} />
              <h2 className="font-semibold">Account & Danger Zone</h2>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 bg-white/5 rounded-xl border border-white/5 flex items-center justify-between">
                <div>
                  <div className="font-bold text-sm">Logged in as</div>
                  <div className="text-xs text-slate-500">{user?.email}</div>
                </div>
                <button 
                  onClick={() => signOut()}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-300 rounded-lg text-xs font-bold transition-all flex items-center gap-2"
                >
                  <LogOut size={14} /> Sign Out
                </button>
              </div>

              <button 
                onClick={handleDeleteData}
                className="w-full p-4 bg-red-500/5 hover:bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-sm font-bold transition-all text-left"
              >
                Delete all my data permanently
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
