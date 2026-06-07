const DOWNLOAD_URL_EXT_RE = /\.(?:7z|appimage|bin|bz2|dmg|deb|exe|gz|iso|msi|pkg|rar|rpm|tar|tgz|txz|xz|zip)(?:[?#]|$)/i

const DOWNLOAD_MIME_TYPES = new Set([
  'application/gzip',
  'application/java-archive',
  'application/octet-stream',
  'application/vnd.android.package-archive',
  'application/vnd.apple.installer+xml',
  'application/vnd.debian.binary-package',
  'application/vnd.microsoft.portable-executable',
  'application/x-7z-compressed',
  'application/x-apple-diskimage',
  'application/x-bzip2',
  'application/x-deb',
  'application/x-gzip',
  'application/x-msdownload',
  'application/x-msi',
  'application/x-rar-compressed',
  'application/x-rpm',
  'application/x-tar',
  'application/x-xz',
  'application/zip'
])

const TEXT_MIME_TYPE_RE =
  /^(?:text\/|application\/(?:ecmascript|javascript|json|rss\+xml|atom\+xml|svg\+xml|toml|xhtml\+xml|xml|x-yaml|yaml|.*\+(?:json|xml))$)/

function normalizeMimeType(value) {
  return String(value || '')
    .split(';')[0]
    .trim()
    .toLowerCase()
}

function headerName(headers, name) {
  const wanted = name.toLowerCase()
  return Object.keys(headers || {}).find(key => key.toLowerCase() === wanted)
}

function headerValues(headers, name) {
  const key = headerName(headers, name)
  const value = key ? headers[key] : undefined

  if (Array.isArray(value)) {
    return value.filter(Boolean).map(String)
  }

  return value ? [String(value)] : []
}

function firstHeaderValue(headers, name) {
  return headerValues(headers, name)[0] || ''
}

function hasAttachmentDisposition(headers) {
  return headerValues(headers, 'content-disposition').some(value => /\battachment\b/i.test(value))
}

function isTextMimeType(value) {
  const mimeType = normalizeMimeType(value)
  return Boolean(mimeType && TEXT_MIME_TYPE_RE.test(mimeType))
}

function isLikelyDownloadMimeType(value) {
  const mimeType = normalizeMimeType(value)
  return Boolean(mimeType && DOWNLOAD_MIME_TYPES.has(mimeType))
}

function isLikelyDownloadUrl(rawUrl) {
  try {
    const url = new URL(String(rawUrl || '').trim())

    return DOWNLOAD_URL_EXT_RE.test(url.pathname)
  } catch {
    return DOWNLOAD_URL_EXT_RE.test(String(rawUrl || '').trim())
  }
}

function classifyResponseHeaders(headers = {}) {
  const contentDisposition = firstHeaderValue(headers, 'content-disposition')
  const contentType = firstHeaderValue(headers, 'content-type')

  if (hasAttachmentDisposition(headers)) {
    return {
      contentDisposition,
      contentType,
      kind: 'download',
      reason: 'content-disposition-attachment'
    }
  }

  if (isLikelyDownloadMimeType(contentType)) {
    return {
      contentDisposition,
      contentType,
      kind: 'download',
      reason: 'download-content-type'
    }
  }

  if (isTextMimeType(contentType)) {
    return {
      contentDisposition,
      contentType,
      kind: 'html',
      reason: 'text-content-type'
    }
  }

  return {
    contentDisposition,
    contentType,
    kind: 'unknown',
    reason: contentType ? 'unhandled-content-type' : 'missing-content-type'
  }
}

function responseHeadersForInlineAttachment(headers, attachmentHeader) {
  return {
    ...headers,
    [attachmentHeader]: headerValues(headers, 'content-disposition').map(value =>
      value.replace(/\battachment\b/gi, 'inline')
    )
  }
}

function backgroundNavigationHeaderPolicy(details = {}) {
  const headers = details.responseHeaders || {}
  const attachmentHeader = headerName(headers, 'content-disposition')
  const contentType = firstHeaderValue(headers, 'content-type')
  const resourceType = String(details.resourceType || '')
  const isDocument = resourceType === 'mainFrame' || resourceType === 'subFrame'

  if (attachmentHeader && hasAttachmentDisposition(headers)) {
    if (isTextMimeType(contentType)) {
      return {
        cancel: false,
        responseHeaders: responseHeadersForInlineAttachment(headers, attachmentHeader)
      }
    }

    return { cancel: true }
  }

  if (isDocument && isLikelyDownloadMimeType(contentType)) {
    return { cancel: true }
  }

  return { cancel: false }
}

module.exports = {
  backgroundNavigationHeaderPolicy,
  classifyResponseHeaders,
  isLikelyDownloadMimeType,
  isLikelyDownloadUrl,
  isTextMimeType
}
