# FinWise Teen 💰

> AI-powered financial planning for young Indians — built for teenagers and young adults who want to start investing smart.

FinWise Teen lets you enter your income, expenses, EMIs, and life goals, then uses **Google Gemini AI** to generate a personalised investment plan across stocks, mutual funds, gold, bonds, REITs, P2P lending, and more — all in Indian context (INR, NIFTY, SGB, etc.).

---

## ✨ Features

- **AI Investment Plan** — Gemini generates a personalised allocation across 8+ asset classes based on your profile
- **Live Market Pulse** — Real-time NIFTY 50, SENSEX, Gold & 10Y Bond yield (Yahoo Finance)
- **5-Step Onboarding** — Income, expenses, ambitions, risk appetite, and retirement goal
- **Wealth Projection** — Visualise your corpus growth over time with interactive charts
- **Share Your Plan** — Public shareable link (`/plan/[userId]`) for anyone to view
- **Google OAuth** — One-click sign in via Google
- **Indian-first** — SGBs, REITs, InvITs, PPF, NPS, P2P lending, US ETFs — assets most Indians miss

---

## 🏗️ Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Charts | Recharts, Framer Motion |
| Backend | FastAPI (Python) |
| AI | Google Gemini 1.5 Pro |
| Database | Supabase (PostgreSQL + Auth) |
| Market Data | Yahoo Finance (yfinance, free) |

---

## � How to Run

### Prerequisites
- Node.js 18+
- Python 3.10+
- A [Supabase](https://supabase.com) project
- A [Gemini API key](https://aistudio.google.com) (free)

### 1. Clone & Configure

```bash
# Root .env — backend config
cp .env.example .env
```

Edit `d:\trial-BNIFTY\.env`:
```env
GEMINI_API_KEY=your-gemini-api-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Edit `d:\trial-BNIFTY\frontend\.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v2
```

### 2. Set Up Database

Run the SQL in `supabase_schema.sql` via your **Supabase Dashboard → SQL Editor**.

Enable **Google OAuth**: Supabase → Authentication → Providers → Google (add your Google Cloud OAuth credentials, redirect URI: `https://your-project.supabase.co/auth/v1/callback`).

### 3. Start the Backend

```powershell
# From d:\trial-BNIFTY
.\venv\Scripts\python run_api.py
```
→ API running at **http://localhost:8000**  
→ Swagger docs at **http://localhost:8000/docs**

### 4. Start the Frontend

```powershell
# From d:\trial-BNIFTY\frontend
npm install
npm run dev
```
→ App running at **http://localhost:3000**

---

## � Project Structure

```
trial-BNIFTY/
├── frontend/                  # Next.js app
│   ├── app/
│   │   ├── page.tsx           # Landing page
│   │   ├── login/             # Login page
│   │   ├── signup/            # Signup page
│   │   ├── onboard/           # 5-step onboarding wizard
│   │   ├── dashboard/         # Main dashboard
│   │   ├── profile/           # Edit profile & regenerate plan
│   │   └── plan/[userId]/     # Public shareable plan
│   ├── components/
│   │   ├── DashboardNav.tsx
│   │   ├── AssetCard.tsx
│   │   ├── MarketPulse.tsx
│   │   └── providers/
│   └── lib/
│       ├── supabase.ts
│       └── utils.ts
├── src/api/
│   └── finwise_routes.py      # All FastAPI v2 endpoints
├── run_api.py                 # FastAPI entry point
├── supabase_schema.sql        # DB schema (run once in Supabase)
└── .env                       # Backend environment variables
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v2/health` | Health check |
| `POST` | `/api/v2/plan/generate` | Generate AI investment plan |
| `GET` | `/api/v2/plan/{userId}/latest` | Get user's latest plan |
| `GET` | `/api/v2/market/pulse` | Live NIFTY, SENSEX, Gold, Bond data |
| `GET` | `/api/v2/market/instruments` | List of all supported investment types |
| `POST` | `/api/v2/profile` | Save user profile |

---

## ⚠️ Disclaimer

FinWise Teen is for **educational purposes only**. This is not SEBI-registered financial advice. Always consult a qualified financial advisor before investing.
