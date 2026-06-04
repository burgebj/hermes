/**
 * React hook for translations. Must be called inside a React component function.
 *
 * Usage:
 *   import { useT } from '@/i18n/useT'
 *   function MyComponent() {
 *     const { t, tf, lang, setLang, toggleLang } = useT()
 *     return <span>{t('settings.sections.model')}</span>
 *   }
 */
import { useStore } from '@nanostores/react'
import { $lang, t as coreT, tf as coreTf, setLang as coreSetLang, toggleLang as coreToggleLang } from './core'

export function useT() {
  const lang = useStore($lang)

  // Bind lang so callers don't have to pass it every time
  const t = (key: string) => coreT(lang, key)
  const tf = (key: string, ...args: (string | number)[]) => coreTf(lang, key, ...args)

  return {
    t,
    tf,
    lang,
    setLang: coreSetLang,
    toggleLang: coreToggleLang,
    $lang,
  }
}
