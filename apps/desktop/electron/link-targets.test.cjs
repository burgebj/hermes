const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

const {
  backgroundNavigationHeaderPolicy,
  classifyResponseHeaders,
  isLikelyDownloadMimeType,
  isLikelyDownloadUrl,
  isTextMimeType
} = require('./link-targets.cjs')

describe('link target safety helpers', () => {
  it('recognizes installer/archive URLs as likely downloads', () => {
    assert.equal(isLikelyDownloadUrl('https://example.com/Hermes-Setup.dmg'), true)
    assert.equal(isLikelyDownloadUrl('https://example.com/release.zip?download=1'), true)
    assert.equal(isLikelyDownloadUrl('https://example.com/docs/getting-started'), false)
  })

  it('classifies attachment responses as downloads', () => {
    assert.deepEqual(
      classifyResponseHeaders({
        'content-disposition': ['attachment; filename="Hermes-Setup.dmg"'],
        'content-type': ['application/octet-stream']
      }),
      {
        contentDisposition: 'attachment; filename="Hermes-Setup.dmg"',
        contentType: 'application/octet-stream',
        kind: 'download',
        reason: 'content-disposition-attachment'
      }
    )
  })

  it('allows normal text/html responses', () => {
    assert.equal(isTextMimeType('text/html; charset=utf-8'), true)
    assert.equal(isLikelyDownloadMimeType('text/html; charset=utf-8'), false)
    assert.equal(
      classifyResponseHeaders({
        'content-type': ['text/html; charset=utf-8']
      }).kind,
      'html'
    )
  })

  it('cancels binary attachment document navigations in background sessions', () => {
    assert.deepEqual(
      backgroundNavigationHeaderPolicy({
        resourceType: 'mainFrame',
        responseHeaders: {
          'Content-Disposition': ['attachment; filename="Hermes-Setup.dmg"'],
          'Content-Type': ['application/octet-stream']
        }
      }),
      { cancel: true }
    )
  })

  it('rewrites text attachments inline for background extraction', () => {
    const policy = backgroundNavigationHeaderPolicy({
      resourceType: 'mainFrame',
      responseHeaders: {
        'Content-Disposition': ['attachment; filename="page.html"'],
        'Content-Type': ['text/html; charset=utf-8']
      }
    })

    assert.equal(policy.cancel, false)
    assert.deepEqual(policy.responseHeaders['Content-Disposition'], ['inline; filename="page.html"'])
  })

  it('cancels octet-stream document navigations even without content-disposition', () => {
    assert.deepEqual(
      backgroundNavigationHeaderPolicy({
        resourceType: 'mainFrame',
        responseHeaders: {
          'Content-Type': ['application/octet-stream']
        }
      }),
      { cancel: true }
    )
  })
})
