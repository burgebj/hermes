import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { $rightRailActiveTabId, RIGHT_RAIL_PREVIEW_TAB_ID } from './layout'
import {
  $filePreviewTabs,
  $filePreviewTarget,
  $previewServerRestart,
  $previewServerRestartStatus,
  $previewTarget,
  $sessionPreviewRegistry,
  beginPreviewServerRestart,
  clearSessionPreviewRegistry,
  closeActiveRightRailTab,
  dismissPreviewTarget,
  getSessionPreviewRecord,
  type PreviewTarget,
  progressPreviewServerRestart,
  setCurrentSessionPreviewTarget,
  syncFilePreviewTabsForSession
} from './preview'
import { $activeSessionId, $selectedStoredSessionId } from './session'

function previewTarget(source: string): PreviewTarget {
  return {
    kind: 'file',
    label: source,
    path: source,
    previewKind: 'html',
    source,
    url: `file://${source}`
  }
}

function withRenderMode(target: PreviewTarget, renderMode: PreviewTarget['renderMode']): PreviewTarget {
  return { ...target, renderMode }
}

describe('preview store', () => {
  beforeEach(() => {
    $previewServerRestart.set(null)
    $activeSessionId.set('session-1')
    $selectedStoredSessionId.set(null)
    window.localStorage.clear()
    clearSessionPreviewRegistry()
  })

  afterEach(() => {
    $previewServerRestart.set(null)
    $activeSessionId.set(null)
    $selectedStoredSessionId.set(null)
    window.localStorage.clear()
    clearSessionPreviewRegistry()
  })

  it('does not notify status subscribers for restart progress text', () => {
    const statuses: string[] = []
    const unsubscribe = $previewServerRestartStatus.subscribe(status => statuses.push(status))

    beginPreviewServerRestart('task-1', 'http://localhost:5174')
    progressPreviewServerRestart('task-1', 'first line')
    progressPreviewServerRestart('task-1', 'second line')
    unsubscribe()

    expect(statuses).toEqual(['idle', 'running'])
  })

  it('persists registered previews and dismissal per session', () => {
    const target = previewTarget('/work/demo.html')

    setCurrentSessionPreviewTarget(target, 'tool-result')

    expect($previewTarget.get()).toEqual(withRenderMode(target, 'preview'))
    expect(getSessionPreviewRecord('session-1')?.normalized).toEqual(withRenderMode(target, 'preview'))
    expect(window.localStorage.getItem('hermes.desktop.sessionPreviews.v1')).toContain('/work/demo.html')

    dismissPreviewTarget()

    expect($previewTarget.get()).toBeNull()
    expect(getSessionPreviewRecord('session-1')).toBeNull()
    expect($sessionPreviewRegistry.get()['session-1']?.[0]?.dismissedAt).toEqual(expect.any(Number))

    setCurrentSessionPreviewTarget(target, 'tool-result')

    expect(getSessionPreviewRecord('session-1')?.dismissedAt).toBeUndefined()
  })

  it('replaces the session preview instead of keeping a back stack', () => {
    const first = previewTarget('/work/first.html')
    const second = previewTarget('/work/second.html')

    setCurrentSessionPreviewTarget(first, 'tool-result')
    setCurrentSessionPreviewTarget(second, 'tool-result')

    expect($sessionPreviewRegistry.get()['session-1']).toHaveLength(1)
    expect(getSessionPreviewRecord('session-1')?.normalized).toEqual(withRenderMode(second, 'preview'))

    dismissPreviewTarget()

    expect($previewTarget.get()).toBeNull()
    expect(getSessionPreviewRecord('session-1')).toBeNull()
    expect($sessionPreviewRegistry.get()['session-1']?.map(record => record.normalized.url)).toEqual([
      'file:///work/second.html'
    ])
  })

  it('keeps file inspection separate from live preview', () => {
    const target = previewTarget('/work/demo.html')
    const preview = previewTarget('/work/live.html')

    setCurrentSessionPreviewTarget(preview, 'tool-result')

    setCurrentSessionPreviewTarget(target, 'manual')

    expect($filePreviewTarget.get()).toEqual(withRenderMode(target, 'source'))
    expect($previewTarget.get()).toEqual(withRenderMode(preview, 'preview'))
    expect(getSessionPreviewRecord('session-1')?.normalized).toEqual(withRenderMode(preview, 'preview'))

    closeActiveRightRailTab()

    expect($filePreviewTarget.get()).toBeNull()
    expect($previewTarget.get()).toEqual(withRenderMode(preview, 'preview'))
  })

  it('keeps file tabs when a live preview opens', () => {
    const file = previewTarget('/work/file.html')
    const live = previewTarget('/work/live.html')

    setCurrentSessionPreviewTarget(file, 'manual')
    setCurrentSessionPreviewTarget(live, 'tool-result')

    expect($filePreviewTabs.get().map(tab => tab.target)).toEqual([withRenderMode(file, 'source')])
    expect($filePreviewTarget.get()).toBeNull()
    expect($rightRailActiveTabId.get()).toBe(RIGHT_RAIL_PREVIEW_TAB_ID)
    expect($previewTarget.get()).toEqual(withRenderMode(live, 'preview'))
  })

  it('drops file preview tabs from other sessions when the active session changes', () => {
    const file = previewTarget('/work/file.html')

    setCurrentSessionPreviewTarget(file, 'manual')

    expect($filePreviewTabs.get()).toHaveLength(1)
    expect($filePreviewTabs.get()[0]?.sessionId).toBe('session-1')
    expect($rightRailActiveTabId.get()).toBe(`file:${file.url}`)

    // Switching to a conversation that does not contain the attachment must
    // dismiss the leaked file tab and fall back to the live preview tab.
    $activeSessionId.set('session-2')
    syncFilePreviewTabsForSession()

    expect($filePreviewTabs.get()).toEqual([])
    expect($rightRailActiveTabId.get()).toBe(RIGHT_RAIL_PREVIEW_TAB_ID)
  })

  it('keeps file preview tabs when re-syncing the active session', () => {
    const file = previewTarget('/work/file.html')

    setCurrentSessionPreviewTarget(file, 'manual')

    // The routing effect re-runs on every registry update within the same
    // session, so syncing the unchanged active session must be a no-op.
    syncFilePreviewTabsForSession()

    expect($filePreviewTabs.get()).toHaveLength(1)
    expect($rightRailActiveTabId.get()).toBe(`file:${file.url}`)
  })

  it('tags file tabs and syncs against the same session derivation', () => {
    const file = previewTarget('/work/file.html')

    // A stored session selection takes precedence over the active session for
    // both tagging and syncing, so a tab opened while a stored session is
    // selected survives a no-op sync.
    $selectedStoredSessionId.set('stored-7')
    setCurrentSessionPreviewTarget(file, 'manual')

    expect($filePreviewTabs.get()[0]?.sessionId).toBe('stored-7')

    syncFilePreviewTabsForSession()
    expect($filePreviewTabs.get()).toHaveLength(1)

    // Clearing the stored selection falls back to the active session, which no
    // longer matches the tab, so it is dropped.
    $selectedStoredSessionId.set(null)
    syncFilePreviewTabsForSession()
    expect($filePreviewTabs.get()).toEqual([])
  })
})
