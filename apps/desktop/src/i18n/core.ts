/**
 * Lightweight i18n core — nanostores-based, no external library.
 *
 * Usage:
 *   import { $lang, t, registerTranslations } from '@/i18n/core'
 *   registerTranslations('ru', { 'hello': 'Привет' })
 *   const label = t($lang.get(), 'hello')  // 'Привет'
 *
 * For React components, use the useT() hook from '@/i18n/useT'.
 */
import { atom } from 'nanostores'

const STORAGE_KEY = 'hermes:lang'

export type Lang = 'en' | 'ru'

function getPersistedLang(): Lang {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'ru' || stored === 'en') return stored
  } catch {}
  return 'en'
}

function persistLang(lang: Lang) {
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {}
}

/** Current language — subscribe to this for reactive updates. */
export const $lang = atom<Lang>(getPersistedLang())

$lang.subscribe((lang) => persistLang(lang))

/** Registered dictionaries: dicts[lang][key] = translated string */
const dicts: Record<string, Record<string, string>> = {}

/**
 * Register translations for a language.
 * Call this at module top level (e.g. in ru.ts or zh.ts).
 */
export function registerTranslations(lang: string, translations: Record<string, string>) {
  if (!dicts[lang]) {
    dicts[lang] = {}
  }
  Object.assign(dicts[lang], translations)
}

/**
 * Translate a key for the given language.
 * Falls back to English readable derivation if not found.
 */
export function t(lang: string, key: string): string {
  // Direct match in requested language
  const val = dicts[lang]?.[key]
  if (val != null) return val

  // Fallback: try English dictionary
  if (lang !== 'en') {
    const enVal = dicts['en']?.[key]
    if (enVal != null) return enVal
  }

  // For config fields, return empty string so the caller falls back to FIELD_LABELS / FIELD_DESCRIPTIONS
  if (key.startsWith('config.field.') || key.startsWith('config.desc.')) {
    return ''
  }

  // Last resort: derive readable text from the full key path
  return keyToReadable(key)
}

/**
 * Translate with positional arguments.
 * Key: 'chat.message_count': 'Сообщений: {0}'
 * Usage: tf('ru', 'chat.message_count', 42) → 'Сообщений: 42'
 */
export function tf(lang: string, key: string, ...args: (string | number)[]): string {
  let str = t(lang, key)
  for (let i = 0; i < args.length; i++) {
    str = str.replace(`{${i}}`, String(args[i]))
  }
  return str
}

/** Set language and trigger reactive updates. */
export function setLang(lang: Lang) {
  $lang.set(lang)
}

/** Toggle between 'en' and 'ru'. */
export function toggleLang() {
  $lang.set($lang.get() === 'ru' ? 'en' : 'ru')
}

function keyToReadable(key: string): string {
  // Use full key path, not just last segment, for better English readability
  return key
    .replace(/\./g, ' ')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim()
}
