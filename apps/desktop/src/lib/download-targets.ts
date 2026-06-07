const DOWNLOAD_URL_EXT_RE = /\.(?:7z|appimage|bin|bz2|dmg|deb|exe|gz|iso|msi|pkg|rar|rpm|tar|tgz|txz|xz|zip)(?:[?#]|$)/i

export function isLikelyDownloadUrl(value: string): boolean {
  const raw = value.trim()

  if (!raw) {
    return false
  }

  try {
    const url = new URL(raw)

    return DOWNLOAD_URL_EXT_RE.test(url.pathname)
  } catch {
    return DOWNLOAD_URL_EXT_RE.test(raw)
  }
}
