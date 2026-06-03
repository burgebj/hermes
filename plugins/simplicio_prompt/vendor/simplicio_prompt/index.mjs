/**
 * simplicio-prompt programmatic API.
 *
 * import { getPrompt, getPromptSection, getPromptPath } from "simplicio-prompt";
 */
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { readFileSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROMPT_PATH = resolve(__dirname, "prompts", "agent-runtime-execution-prompt.md");

export function getPromptPath() {
  return PROMPT_PATH;
}

export function getPrompt() {
  return readFileSync(PROMPT_PATH, "utf-8");
}

export function getPromptSection() {
  const full = getPrompt();
  const lines = full.split("\n");
  const startIdx = lines.findIndex((l) => l.trim() === "## Prompt");
  if (startIdx === -1) return full;
  const body = lines.slice(startIdx + 1);
  const endIdx = body.findIndex((l) => /^##\s+/.test(l));
  const section = endIdx === -1 ? body : body.slice(0, endIdx);
  return section.join("\n").trim() + "\n";
}

export default { getPrompt, getPromptSection, getPromptPath };
