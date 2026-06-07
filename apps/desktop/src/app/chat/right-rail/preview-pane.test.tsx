import { act, cleanup, render } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { PreviewPane } from './preview-pane'

describe('PreviewPane console state', () => {
  afterEach(() => {
    cleanup()
  })

  it('does not rebuild the pane titlebar group for streamed console logs', () => {
    const setTitlebarToolGroup = vi.fn()

    const rendered = render(
      <PreviewPane
        setTitlebarToolGroup={setTitlebarToolGroup}
        target={{
          kind: 'url',
          label: 'Preview',
          source: 'http://localhost:5174',
          url: 'http://localhost:5174'
        }}
      />
    )

    const initialCalls = setTitlebarToolGroup.mock.calls.length
    const webview = rendered.container.querySelector('webview')

    expect(webview).toBeInstanceOf(HTMLElement)

    act(() => {
      webview?.dispatchEvent(
        Object.assign(new Event('console-message'), {
          level: 0,
          message: 'streamed log line',
          sourceId: 'http://localhost:5174/src/main.tsx'
        })
      )
    })

    expect(setTitlebarToolGroup).toHaveBeenCalledTimes(initialCalls)
  })

  it('does not mount a webview for likely download targets', () => {
    const rendered = render(
      <PreviewPane
        target={{
          kind: 'url',
          label: 'Hermes Setup',
          source: 'https://hermes-assets.nousresearch.com/Hermes-Setup.dmg',
          url: 'https://hermes-assets.nousresearch.com/Hermes-Setup.dmg'
        }}
      />
    )

    expect(rendered.container.querySelector('webview')).toBeNull()
    expect(rendered.container.textContent).toContain('downloadable file')
  })
})
