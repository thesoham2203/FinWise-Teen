const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v2'

export interface MarketPulseData {
    nifty50: { value: number; change: number; changePercent: number }
    sensex: { value: number; change: number; changePercent: number }
    gold: { value: number; change: number; changePercent: number }
    bond10y: { value: number }
    source: string
    timestamp: string
}

export interface MarketHistoryPoint {
    date: string
    close: number
}

export interface MarketHistory {
    symbol: string
    history: MarketHistoryPoint[]
    count: number
}

export async function getMarketPulse(): Promise<MarketPulseData | null> {
    try {
        const res = await fetch(`${API_BASE_URL}/market/pulse`, { cache: 'no-store' })
        if (!res.ok) throw new Error('Failed to fetch market pulse')
        return await res.ok ? res.json() : null
    } catch (err) {
        console.error('Market Pulse Fetch Error:', err)
        return null
    }
}

export async function getMarketHistory(symbol: string): Promise<MarketHistory | null> {
    try {
        const res = await fetch(`${API_BASE_URL}/market/history/${symbol}`, { cache: 'no-store' })
        if (!res.ok) throw new Error('Failed to fetch market history')
        return await res.json()
    } catch (err) {
        console.error(`Market History Fetch Error (${symbol}):`, err)
        return null
    }
}
