import { describe, expect, it } from 'vitest'
import { parseSlashCommand, coerceThinkingText } from './chat-runtime'

describe('parseSlashCommand', () => {
  it('should parse simple command without arguments', () => {
    const result = parseSlashCommand('/help')
    expect(result).toEqual({ name: 'help', arg: '' })
  })

  it('should parse command with single-line argument', () => {
    const result = parseSlashCommand('/goal Write a Python script')
    expect(result).toEqual({ name: 'goal', arg: 'Write a Python script' })
  })

  it('should parse command with multi-line argument (with newline)', () => {
    const result = parseSlashCommand('/goal Write a Python\nthat prints Hello')
    expect(result).toEqual({ name: 'goal', arg: 'Write a Python\nthat prints Hello' })
  })

  it('should handle multiple newlines in argument', () => {
    const result = parseSlashCommand('/goal Line 1\nLine 2\nLine 3')
    expect(result).toEqual({ name: 'goal', arg: 'Line 1\nLine 2\nLine 3' })
  })

  it('should handle command with leading slashes', () => {
    const result = parseSlashCommand('//goal Write something')
    expect(result).toEqual({ name: 'goal', arg: 'Write something' })
  })

  it('should handle command with trailing whitespace in argument', () => {
    const result = parseSlashCommand('/goal Some text  ')
    expect(result).toEqual({ name: 'goal', arg: 'Some text' })
  })

  it('should handle command with leading and trailing whitespace', () => {
    const result = parseSlashCommand('  /goal Write text  ')
    expect(result).toEqual({ name: '', arg: '' })
  })

  it('should handle tabs and newlines mixed in argument', () => {
    const result = parseSlashCommand('/goal\tWrite something\nand more')
    expect(result).toEqual({ name: 'goal', arg: 'Write something\nand more' })
  })

  it('should parse /goal with comprehensive multiline example', () => {
    const input = `/goal Create a comprehensive testing framework
that supports unit tests
and integration tests
with clear documentation`
    const result = parseSlashCommand(input)
    expect(result.name).toBe('goal')
    expect(result.arg).toContain('Create a comprehensive testing framework')
    expect(result.arg).toContain('unit tests')
    expect(result.arg).toContain('integration tests')
    expect(result.arg).toContain('clear documentation')
  })
})

describe('coerceThinkingText', () => {
  it('strips streaming status prefixes from thinking deltas', () => {
    expect(coerceThinkingText("◉_◉ processing... checking the user's request")).toBe("checking the user's request")
    expect(coerceThinkingText('(¬‿¬) analyzing... reading the file')).toBe('reading the file')
  })

  it('drops empty thinking rewrite placeholder text', () => {
    expect(
      coerceThinkingText(
        "◉_◉ processing... I don't see any current rewritten thinking or next thinking to process. Could you provide the thinking content you'd like me to rewrite?"
      )
    ).toBe('')
  })
})
