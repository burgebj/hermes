import test from 'node:test';
import assert from 'node:assert/strict';
import {
  formatPairingCodeForDisplay,
  parsePairWithNumberArg,
  validateE164ForPairing,
} from './pairing-args.js';

test('validateE164ForPairing accepts E.164 with +', () => {
  assert.deepEqual(validateE164ForPairing('+15551234567'), { ok: true, digits: '15551234567' });
});

test('validateE164ForPairing accepts E.164 without +', () => {
  assert.deepEqual(validateE164ForPairing('15551234567'), { ok: true, digits: '15551234567' });
});

test('validateE164ForPairing accepts UK-format E.164 with +', () => {
  assert.deepEqual(validateE164ForPairing('+447911123456'), { ok: true, digits: '447911123456' });
});

test('validateE164ForPairing rejects leading zero', () => {
  assert.equal(validateE164ForPairing('+015551234567').ok, false);
});

test('validateE164ForPairing rejects spaces', () => {
  assert.equal(validateE164ForPairing('+1 555 123 4567').ok, false);
});

test('validateE164ForPairing rejects hyphenated numbers', () => {
  assert.equal(validateE164ForPairing('+1-555-1234567').ok, false);
});

test('validateE164ForPairing rejects too-short numbers', () => {
  assert.equal(validateE164ForPairing('+155512345').ok, false);
});

test('formatPairingCodeForDisplay hyphenates length-8 codes', () => {
  assert.equal(formatPairingCodeForDisplay('abcdefgh'), 'ABCD-EFGH');
});

test('formatPairingCodeForDisplay leaves non-8 length unchanged', () => {
  assert.equal(formatPairingCodeForDisplay('abc'), 'ABC');
});

test('parsePairWithNumberArg returns found false when absent', () => {
  assert.deepEqual(parsePairWithNumberArg(['node', 'bridge.js']), { found: false, value: null });
});

test('parsePairWithNumberArg parses value', () => {
  assert.deepEqual(
    parsePairWithNumberArg(['node', 'bridge.js', '--pair-with-number', '+15551234567']),
    {
      found: true,
      value: '+15551234567',
    },
  );
});

test('parsePairWithNumberArg errors when value missing', () => {
  const r = parsePairWithNumberArg(['node', 'bridge.js', '--pair-with-number']);
  assert.equal(r.found, true);
  assert.ok(r.error);
});

test('parsePairWithNumberArg errors when value is empty', () => {
  const r = parsePairWithNumberArg(['node', 'bridge.js', '--pair-with-number', '']);
  assert.equal(r.found, true);
  assert.ok(r.error);
});
