import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number, currency: string = 'INR'): string {
    if (amount === undefined || amount === null || Number.isNaN(amount)) {
        return currency === 'USD' ? '$0' : '₹0'
    }
    if (currency === 'USD') {
        if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`
        if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`
        return `$${amount.toFixed(0)}`
    }
    // Default INR
    if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`
    if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`
    return `₹${amount.toFixed(0)}`
}

export function formatFullCurrency(amount: number, currency: string = 'INR'): string {
    if (amount === undefined || amount === null || Number.isNaN(amount)) return currency === 'USD' ? '$0' : '₹0'
    return new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-US', {
        style: 'currency',
        currency: currency,
        maximumFractionDigits: 0,
    }).format(amount)
}

