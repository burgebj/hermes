import { describe, expect, it, vi } from 'vitest'

import { isUsableClipboardText, readClipboardText, writeClipboardText } from '../lib/clipboard.js'

const NUL = '\u0000'
const SOH = '\u0001'
const STX = '\u0002'
const ETX = '\u0003'
const EOT = '\u0004'
const REPLACEMENT = '\ufffd'

describe('isUsableClipboardText — gap coverage', () => {
  it('rejects null input', () => {
    expect(isUsableClipboardText(null)).toBe(false)
  })

  it('rejects strings containing a NUL byte even when surrounding text is printable', () => {
    expect(isUsableClipboardText(`hello${NUL}world`)).toBe(false)
  })

  it('treats newline, carriage-return, and tab as non-suspicious whitespace controls', () => {
    expect(isUsableClipboardText('line1\nline2\r\nline3\ttabbed')).toBe(true)
  })

  it('accepts the absolute floor of 2 stray control chars in short text', () => {
    expect(isUsableClipboardText(`hi${SOH}${STX}`)).toBe(true)
  })

  it('rejects short text once stray control chars exceed the absolute floor of 2', () => {
    expect(isUsableClipboardText(`hi${SOH}${STX}${ETX}`)).toBe(false)
  })

  it('scales tolerance to 2% of length on long text', () => {
    const longClean = 'a'.repeat(200)
    expect(isUsableClipboardText(longClean + `${SOH}${STX}${ETX}${EOT}`)).toBe(true)
  })

  it('rejects long text that breaches the 2% suspicious-char ceiling', () => {
    const longClean = 'a'.repeat(100)
    expect(isUsableClipboardText(longClean + SOH.repeat(10))).toBe(false)
  })

  it('counts U+FFFD replacement chars as suspicious', () => {
    expect(isUsableClipboardText(`a${REPLACEMENT}${REPLACEMENT}${REPLACEMENT}`)).toBe(false)
  })
})

describe('readClipboardText — gap coverage', () => {
  it('falls back from powershell.exe to xclip on WSL when powershell.exe rejects', async () => {
    const run = vi
      .fn()
      .mockRejectedValueOnce(new Error('powershell.exe missing'))
      .mockResolvedValueOnce({ stdout: 'from xclip after wsl miss\n' })

    await expect(
      readClipboardText('linux', run, { WSL_INTEROP: '/tmp/sock' } as NodeJS.ProcessEnv)
    ).resolves.toBe('from xclip after wsl miss\n')
    expect(run).toHaveBeenNthCalledWith(
      1,
      'powershell.exe',
      expect.arrayContaining(['Get-Clipboard -Raw']),
      expect.anything()
    )
    expect(run).toHaveBeenNthCalledWith(2, 'xclip', ['-selection', 'clipboard', '-out'], expect.anything())
  })

  it('returns null when the backend resolves with non-string stdout', async () => {
    const run = vi.fn().mockResolvedValue({ stdout: undefined as unknown as string })

    await expect(readClipboardText('darwin', run)).resolves.toBeNull()
  })

  it('on bare Linux without Wayland or WSL goes straight to xclip (no wl-paste attempt)', async () => {
    const run = vi.fn().mockResolvedValue({ stdout: 'plain x11\n' })

    await expect(readClipboardText('linux', run, {} as NodeJS.ProcessEnv)).resolves.toBe('plain x11\n')
    expect(run).toHaveBeenCalledTimes(1)
    expect(run).toHaveBeenCalledWith('xclip', ['-selection', 'clipboard', '-out'], expect.anything())
  })
})

describe('writeClipboardText — gap coverage', () => {
  function makeChild(stdinEnd: ReturnType<typeof vi.fn>, exitCode: number) {
    const child = {
      once: vi.fn((event: string, cb: (code?: number) => void) => {
        if (event === 'close') {
          cb(exitCode)
        }

        return child
      }),
      stdin: { end: stdinEnd }
    }

    return child
  }

  it('forwards an empty string to the backend without short-circuiting', async () => {
    const stdin = vi.fn()
    const start = vi.fn().mockReturnValue(makeChild(stdin, 0))

    await expect(writeClipboardText('', 'darwin', start as never)).resolves.toBe(true)
    expect(start).toHaveBeenCalledWith('pbcopy', [], expect.anything())
    expect(stdin).toHaveBeenCalledWith('')
  })

  it('returns false on bare Linux when both xclip and xsel exit non-zero', async () => {
    const stdin = vi.fn()
    const start = vi.fn().mockReturnValue(makeChild(stdin, 1))

    await expect(writeClipboardText('hello', 'linux', start as never, {})).resolves.toBe(false)
    expect(start).toHaveBeenNthCalledWith(1, 'xclip', ['-selection', 'clipboard', '-in'], expect.anything())
    expect(start).toHaveBeenNthCalledWith(2, 'xsel', ['--clipboard', '--input'], expect.anything())
  })
})
