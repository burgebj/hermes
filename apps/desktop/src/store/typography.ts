import { atom } from 'nanostores'

export type DensityMode = 'compact' | 'default' | 'comfortable'

const FONT_SIZE_KEY = 'hermes.desktop.typography.fontSize'
const MESSAGE_FONT_SIZE_KEY = 'hermes.desktop.typography.messageFontSize'
const DENSITY_KEY = 'hermes.desktop.typography.density'

const DEFAULT_FONT_SIZE = 14
const DEFAULT_MESSAGE_FONT_SIZE = 13
const DEFAULT_DENSITY: DensityMode = 'default'

const MIN_FONT_SIZE = 12
const MAX_FONT_SIZE = 18

function loadNumber(key: string, fallback: number): number {
  if (typeof window === 'undefined') return fallback

  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return fallback
    const val = Number(raw)
    return Number.isFinite(val) ? val : fallback
  } catch {
    return fallback
  }
}

function loadDensity(): DensityMode {
  if (typeof window === 'undefined') return DEFAULT_DENSITY

  try {
    const raw = window.localStorage.getItem(DENSITY_KEY) as DensityMode | null
    if (raw === 'compact' || raw === 'comfortable') return raw
    return DEFAULT_DENSITY
  } catch {
    return DEFAULT_DENSITY
  }
}

export const $baseFontSize = atom(loadNumber(FONT_SIZE_KEY, DEFAULT_FONT_SIZE))
export const $messageFontSize = atom(loadNumber(MESSAGE_FONT_SIZE_KEY, DEFAULT_MESSAGE_FONT_SIZE))
export const $densityMode = atom<DensityMode>(loadDensity())

$baseFontSize.subscribe(val => {
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(FONT_SIZE_KEY, String(val))
    } catch {}
  }
})

$messageFontSize.subscribe(val => {
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(MESSAGE_FONT_SIZE_KEY, String(val))
    } catch {}
  }
})

$densityMode.subscribe(val => {
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(DENSITY_KEY, val)
    } catch {}
  }
})

export function setBaseFontSize(px: number) {
  $baseFontSize.set(Math.round(Math.min(MAX_FONT_SIZE, Math.max(MIN_FONT_SIZE, px))))
}

export function setMessageFontSize(px: number) {
  $messageFontSize.set(Math.round(Math.min(MAX_FONT_SIZE, Math.max(MIN_FONT_SIZE, px))))
}

export function setDensityMode(mode: DensityMode) {
  $densityMode.set(mode)
}

export function getDensityScale(mode: DensityMode): number {
  switch (mode) {
    case 'compact':
      return 0.85
    case 'comfortable':
      return 1.15
    default:
      return 1
  }
}
