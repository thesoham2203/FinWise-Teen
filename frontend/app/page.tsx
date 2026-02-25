'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight, TrendingUp, Brain, Shield, Sparkles, Star, ChevronRight } from 'lucide-react'
import Navbar from '@/components/Navbar'

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Advice',
    desc: 'Gemini AI analyses your income, EMIs, and goals to craft a personalised investment roadmap just for you.',
    color: 'from-violet-500/20 to-indigo-500/20',
    border: 'border-violet-500/20',
    iconColor: 'text-violet-400',
  },
  {
    icon: TrendingUp,
    title: 'All Asset Classes',
    desc: 'Stocks, mutual funds, bonds, gold, REITs, P2P lending, crypto, FDs — we cover investments most advisors skip.',
    color: 'from-emerald-500/20 to-teal-500/20',
    border: 'border-emerald-500/20',
    iconColor: 'text-emerald-400',
  },
  {
    icon: Shield,
    title: 'Retirement Planner',
    desc: 'Tell us when you want to retire. We calculate exactly how much to invest monthly and track your progress.',
    color: 'from-amber-500/20 to-orange-500/20',
    border: 'border-amber-500/20',
    iconColor: 'text-amber-400',
  },
]

const investmentTypes = [
  { name: 'NIFTY 50 Index', category: 'Stocks', return: '12-15%', risk: 'Medium' },
  { name: 'Flexi Cap MF', category: 'Mutual Funds', return: '14-18%', risk: 'Medium-High' },
  { name: 'Govt Bonds', category: 'Bonds', return: '7-8%', risk: 'Very Low' },
  { name: 'Sovereign Gold Bond', category: 'Gold', return: '8-12%', risk: 'Low' },
  { name: 'REITs', category: 'Real Estate', return: '8-11%', risk: 'Medium' },
  { name: 'P2P Lending', category: 'Alternative', return: '10-14%', risk: 'High' },
]

const testimonials = [
  { name: 'Arjun, 19', text: 'Started SIPs at ₹2K/month. FinWise showed me I can retire by 48 if I stay consistent!', stars: 5 },
  { name: 'Priya, 23', text: 'Never knew about REITs or P2P lending. This app opened up a whole new world of investing.', stars: 5 },
  { name: 'Rohan, 17', text: 'Even as a student with ₹5000/month income, I have a proper financial plan now.', stars: 5 },
]

export default function LandingPage() {
  return (
    <main className="min-h-screen overflow-x-hidden">
      <Navbar />

      {/* Hero */}
      <section className="relative pt-28 pb-32 px-4 flex flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="relative z-10 max-w-4xl"
        >
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-2 text-xs font-bold text-indigo-300 mb-8 uppercase tracking-widest glow-primary">
            <Sparkles size={12} />
            Built for Young India · Powered by Gemini AI
          </div>

          <h1 className="text-6xl md:text-8xl font-bold leading-tight mb-8 font-jakarta tracking-tight">
            Your Money,{' '}
            <span className="gradient-text glow-text">Your Future</span>
            <br />— Start at 16.
          </h1>

          <p className="text-xl md:text-2xl text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed font-light">
            Tell us your salary, dreams, and goals.
            Our AI builds a personalized roadmap across <strong className="text-white">stocks, bonds, gold, and more</strong>.
          </p>

          <div className="flex flex-col sm:flex-row gap-5 justify-center">
            <Link href="/signup">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="btn-primary flex items-center gap-3 text-lg px-10 py-5"
              >
                Get Started Free <ArrowRight size={20} />
              </motion.button>
            </Link>
          </div>

          {/* Stats bar */}
          <div className="flex flex-wrap justify-center gap-12 mt-20 text-center">
            {[
              { value: '15+', label: 'Asset Classes' },
              { value: '₹0', label: 'Cost to Start' },
              { value: 'AI', label: 'Advisor' },
              { value: '∞', label: 'Possibilities' },
            ].map((s) => (
              <div key={s.label}>
                <div className="text-4xl font-bold gradient-text mb-1">{s.value}</div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">{s.label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="py-24 px-4 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold font-jakarta mb-4">
            Everything you need to <span className="gradient-text">build wealth early</span>
          </h2>
          <p className="text-slate-400 text-lg">Most teenagers don&#39;t know where to start. We make it simple.</p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card p-8 group cursor-default"
            >
              <div className={`w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mb-6 transition-transform group-hover:scale-110 group-hover:rotate-3 ${f.iconColor}`}>
                <f.icon size={28} className="glow-primary" />
              </div>
              <h3 className="text-xl font-bold mb-3">{f.title}</h3>
              <p className="text-slate-400 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Investment types ticker */}
      <section className="py-16 px-4 bg-gradient-to-r from-transparent via-indigo-950/30 to-transparent">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-3 font-jakarta">
            All Investment Types — Even the <span className="gradient-text-emerald">lesser-known ones</span>
          </h2>
          <p className="text-slate-400 text-center text-sm mb-10">We recommend across 15+ asset classes, not just stocks and FDs.</p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {investmentTypes.map((inv, i) => (
              <motion.div
                key={inv.name}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="glass-card p-4 text-center hover:border-indigo-500/30 transition-colors"
              >
                <div className="text-xs text-indigo-400 mb-1 font-medium">{inv.category}</div>
                <div className="text-sm font-semibold text-white mb-2">{inv.name}</div>
                <div className="text-xs text-emerald-400 font-medium">{inv.return} p.a.</div>
                <div className="text-xs text-slate-500 mt-1">Risk: {inv.risk}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-4 max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12 font-jakarta">
          How it works
        </h2>
        <div className="relative">
          {/* Connecting line */}
          <div className="absolute left-6 top-8 bottom-8 w-px bg-gradient-to-b from-indigo-500/50 via-violet-500/50 to-emerald-500/50 hidden md:block" />
          <div className="space-y-8">
            {[
              { n: '01', title: 'Create your account', desc: 'Sign up with Google in 10 seconds. Completely free.' },
              { n: '02', title: 'Fill your financial profile', desc: 'Income, EMIs, savings, ambitions, and when you want to retire.' },
              { n: '03', title: 'Get your AI plan', desc: 'Gemini AI analyses your data + live market conditions to suggest the perfect allocation.' },
              { n: '04', title: 'Track and grow', desc: 'Follow your plan, update regularly, share with family. Watch your wealth compound.' },
            ].map((step, i) => (
              <motion.div
                key={step.n}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-6"
              >
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center font-bold text-sm z-10">
                  {step.n}
                </div>
                <div className="glass-card p-5 flex-1">
                  <div className="font-semibold text-white mb-1">{step.title}</div>
                  <div className="text-slate-400 text-sm">{step.desc}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-16 px-4 bg-gradient-to-r from-transparent via-violet-950/20 to-transparent">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-10 font-jakarta">Loved by young investors</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass-card p-6"
              >
                <div className="flex gap-1 mb-3">
                  {Array.from({ length: t.stars }).map((_, j) => (
                    <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                  ))}
                </div>
                <p className="text-slate-300 text-sm leading-relaxed mb-4">&#34;{t.text}&#34;</p>
                <div className="text-sm font-semibold text-indigo-400">{t.name}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 px-4 text-center relative">
        <div className="hero-orb w-[500px] h-[300px] bg-indigo-600/15 top-0 left-1/2 -translate-x-1/2" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative z-10 max-w-2xl mx-auto"
        >
          <h2 className="text-4xl font-bold font-jakarta mb-4">
            Start building wealth <span className="gradient-text">today</span>
          </h2>
          <p className="text-slate-400 mb-8">
            The earlier you start, the more compounding does the work. Don&#39;t wait.
          </p>
          <Link href="/signup">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="btn-primary text-base px-10 py-4 flex items-center gap-2 mx-auto"
            >
              Create Free Account <ChevronRight size={18} />
            </motion.button>
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-4 text-center text-sm text-slate-600">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-3">
          <div className="font-bold text-slate-400">FinWise Teen</div>
          <div>For educational purposes. Not SEBI-registered financial advice.</div>
          <div className="flex gap-4">
            <Link href="/login" className="hover:text-slate-400 transition-colors">Login</Link>
            <Link href="/signup" className="hover:text-slate-400 transition-colors">Sign Up</Link>
          </div>
        </div>
      </footer>
    </main>
  )
}
