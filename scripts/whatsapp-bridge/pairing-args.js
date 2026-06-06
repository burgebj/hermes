/** E.164-like phone number for pairing: country code plus 10–15 digits total. */
export const E164_PAIRING_REGEX = /^\+?[1-9]\d{9,14}$/;

/**
 * @param {string} raw - CLI value passed to `--pair-with-number`
 * @returns {{ ok: true, digits: string } | { ok: false, error: string }}
 */
export function validateE164ForPairing(raw) {
  const s = String(raw ?? '').trim();
  if (!E164_PAIRING_REGEX.test(s)) {
    return {
      ok: false,
      error:
        'Invalid phone number. Use 10–15 digits total with country code (e.g. +15551234567): digits only, optional leading +.',
    };
  }
  const digits = s.startsWith('+') ? s.slice(1) : s;
  return { ok: true, digits };
}

/**
 * @param {string} code - Raw pairing code from Baileys (typically 8 Crockford chars)
 */
export function formatPairingCodeForDisplay(code) {
  const c = String(code || '').replace(/\s/g, '').toUpperCase();
  if (c.length === 8) return `${c.slice(0, 4)}-${c.slice(4)}`;
  return c;
}

/**
 * @param {string[]} argv - e.g. process.argv
 */
export function parsePairWithNumberArg(argv) {
  const args = argv.slice(2);
  const idx = args.indexOf('--pair-with-number');
  if (idx === -1) return { found: false, value: null };
  const v = args[idx + 1];
  if (!v || v.startsWith('--')) {
    return {
      found: true,
      value: null,
      error:
        '--pair-with-number requires a phone number argument (E.164, e.g. +15551234567)',
    };
  }
  return { found: true, value: v };
}
