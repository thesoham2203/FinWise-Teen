-- FinWise Teen — Supabase Schema
-- Run this in your Supabase SQL Editor (Database > SQL Editor)

-- User financial profiles
CREATE TABLE IF NOT EXISTS public.user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  age INT,
  city TEXT,
  occupation TEXT DEFAULT 'student',
  monthly_income NUMERIC DEFAULT 0,
  monthly_expenses NUMERIC DEFAULT 0,
  monthly_emis NUMERIC DEFAULT 0,
  current_savings NUMERIC DEFAULT 0,
  dream_job TEXT,
  target_income_5yr NUMERIC DEFAULT 0,
  risk_appetite TEXT DEFAULT 'moderate',
  investment_horizon_years INT DEFAULT 10,
  retirement_age INT DEFAULT 55,
  target_corpus NUMERIC DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id)
);

-- AI-generated investment plans
CREATE TABLE IF NOT EXISTS public.investment_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  profile_snapshot JSONB,
  allocation JSONB,
  monthly_investment NUMERIC,
  reasoning TEXT,
  retirement_projection JSONB,
  is_public BOOLEAN DEFAULT false,
  generated_at TIMESTAMPTZ DEFAULT now()
);

-- Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investment_plans ENABLE ROW LEVEL SECURITY;

-- Users can only see/edit their own profile
CREATE POLICY "Users manage own profile" ON public.user_profiles
  FOR ALL USING (auth.uid() = user_id);

-- Users can view their own plans; public plans visible to all
CREATE POLICY "Users view own plans" ON public.investment_plans
  FOR SELECT USING (auth.uid() = user_id OR is_public = true);

CREATE POLICY "Users insert own plans" ON public.investment_plans
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_profiles_updated_at
  BEFORE UPDATE ON public.user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Grant permissions
GRANT ALL ON public.user_profiles TO anon, authenticated;
GRANT ALL ON public.investment_plans TO anon, authenticated;
