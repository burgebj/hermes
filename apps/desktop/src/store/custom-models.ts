import { atom } from 'nanostores'

import { persistString, storedString } from '@/lib/storage'

const STORAGE_KEY = 'hermes.desktop.custom-models'

export interface CustomModel {
  model: string
  provider: string
}

function load(): CustomModel[] {
  const raw = storedString(STORAGE_KEY)

  if (!raw) {
    return []
  }

  try {
    const parsed = JSON.parse(raw)

    return Array.isArray(parsed)
      ? parsed.filter((x): x is CustomModel => typeof x?.provider === 'string' && typeof x?.model === 'string')
      : []
  } catch {
    return []
  }
}

function persist(models: CustomModel[]): void {
  persistString(STORAGE_KEY, JSON.stringify(models))
}

export const $customModels = atom<CustomModel[]>(load())

export function addCustomModel(provider: string, model: string): void {
  const current = $customModels.get()

  if (current.some(m => m.provider === provider && m.model === model)) {
    return
  }

  const next = [...current, { model, provider }]
  $customModels.set(next)
  persist(next)
}

export function removeCustomModel(provider: string, model: string): void {
  const next = $customModels.get().filter(m => !(m.provider === provider && m.model === model))
  $customModels.set(next)
  persist(next)
}

export function getCustomModelsForProvider(provider: string): string[] {
  return $customModels
    .get()
    .filter(m => m.provider === provider)
    .map(m => m.model)
}
