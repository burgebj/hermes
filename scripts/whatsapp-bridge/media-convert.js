// Audio conversion helper for the WhatsApp bridge.
//
// WhatsApp only renders a native voice bubble (ptt) for ogg/opus audio, so the
// bridge transcodes other formats (mp3/wav/m4a from Edge TTS, NeuTTS, etc.)
// with ffmpeg before sending.
//
// SECURITY: the file paths MUST be handed to ffmpeg as discrete argv entries
// via execFileSync — never interpolated into a shell command string. A media
// filename reaching /send-media is attacker-influenceable (it just has to name
// a real file on disk), and inside a double-quoted shell token JSON.stringify
// does NOT neutralise `$(...)`, backticks or `$VAR`, so the previous
// `execSync(\`ffmpeg ... ${JSON.stringify(filePath)} ...\`)` form allowed
// command execution on the bridge host. execFileSync spawns ffmpeg directly
// with no shell, so metacharacters in a path are inert.

import { execFileSync } from 'child_process';

// The ffmpeg argument vector for "transcode <input> to mono 48kHz opus in an
// ogg container at <output>". Kept separate so it can be asserted in tests.
export function buildOpusFfmpegArgs(inputPath, outputPath) {
  return ['-y', '-i', inputPath, '-ar', '48000', '-ac', '1', '-c:a', 'libopus', outputPath];
}

// Convert an audio file to ogg/opus. `exec` is injectable purely so tests can
// observe the call without invoking the real ffmpeg binary; production always
// uses execFileSync (no shell).
export function convertAudioToOpus(inputPath, outputPath, exec = execFileSync) {
  return exec('ffmpeg', buildOpusFfmpegArgs(inputPath, outputPath), { timeout: 30000, stdio: 'pipe' });
}
