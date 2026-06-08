import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';

import { buildOpusFfmpegArgs, convertAudioToOpus } from './media-convert.js';

test('buildOpusFfmpegArgs returns a discrete argv array with the paths as standalone entries', () => {
  const args = buildOpusFfmpegArgs('/tmp/in.mp3', '/tmp/out.ogg');
  assert.ok(Array.isArray(args));
  assert.deepEqual(args, ['-y', '-i', '/tmp/in.mp3', '-ar', '48000', '-ac', '1', '-c:a', 'libopus', '/tmp/out.ogg']);
});

test('convertAudioToOpus invokes ffmpeg via argv, never a shell command string', () => {
  // Regression guard for the command-injection fix: if someone reverts to
  // `execSync(\`ffmpeg ... ${filePath} ...\`)`, exec would be called with a
  // single string and no argv array, and this assertion would fail.
  const calls = [];
  convertAudioToOpus('/tmp/in.mp3', '/tmp/out.ogg', (cmd, args, opts) => calls.push({ cmd, args, opts }));

  assert.equal(calls.length, 1);
  assert.equal(calls[0].cmd, 'ffmpeg');
  assert.ok(Array.isArray(calls[0].args));
  // No single argument carries a packed command line.
  assert.ok(!calls[0].args.some((a) => a.includes('ffmpeg -y')));
});

test('a media path containing shell metacharacters is passed literally and never executed', () => {
  const dir = mkdtempSync(path.join(os.tmpdir(), 'hermes-wa-media-'));
  try {
    const sentinel = path.join(dir, 'PWNED');
    // A real, existing file whose NAME is a command substitution (kept to a
    // single path component — no slashes — so it is a valid filename).
    // existsSync() in the bridge happily accepts it, so it reaches the converter.
    const malicious = path.join(dir, 'voice$(touch PWNED).wav');
    writeFileSync(malicious, 'audio-bytes');
    const out = path.join(dir, 'out.ogg');

    // Stand-in for the ffmpeg binary: a real child process spawned with
    // execFileSync (no shell) that copies its -i input to its output. If the
    // path were ever interpolated into a shell string, $(touch …) would run
    // and create the sentinel; with argv passing it cannot.
    const copyExec = (_cmd, ffArgs) => {
      const input = ffArgs[ffArgs.indexOf('-i') + 1];
      const output = ffArgs[ffArgs.length - 1];
      execFileSync(process.execPath, [
        '-e',
        'const fs=require("fs");fs.writeFileSync(process.argv[2],fs.readFileSync(process.argv[1]))',
        input,
        output,
      ], { cwd: dir });
    };

    convertAudioToOpus(malicious, out, copyExec);

    assert.equal(existsSync(sentinel), false, 'command substitution must not execute');
    assert.equal(readFileSync(out, 'utf8'), 'audio-bytes');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
