#!/usr/bin/env node
/**
 * simplicio-prompt CLI
 *
 * Prints the Tuple-Space + Yool execution prompt, or installs it into a target
 * agent instruction file (AGENTS.md, CLAUDE.md, .cursorrules, etc.).
 *
 * Usage:
 *   npx simplicio-prompt                 # print prompt to stdout
 *   npx simplicio-prompt --install       # install into CLAUDE.md (default)
 *   npx simplicio-prompt --install AGENTS.md
 *   npx simplicio-prompt --install .cursorrules
 *   npx simplicio-prompt --raw           # print only the Prompt section
 *   npx simplicio-prompt --path          # print the path to the prompt file
 */
import { fileURLToPath } from "node:url";
import { dirname, resolve, basename } from "node:path";
import { existsSync, readFileSync, writeFileSync, appendFileSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PKG_ROOT = resolve(__dirname, "..");
const PROMPT_PATH = resolve(PKG_ROOT, "prompts", "agent-runtime-execution-prompt.md");

const MARK_START = "<!-- simplicio-prompt:start -->";
const MARK_END = "<!-- simplicio-prompt:end -->";

function parseArgs(argv) {
  const args = { mode: "print", target: null, raw: false };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === "--install") {
      args.mode = "install";
      const next = argv[i + 1];
      if (next && !next.startsWith("--")) {
        args.target = next;
        i++;
      }
    } else if (k === "--raw") {
      args.raw = true;
    } else if (k === "--path") {
      args.mode = "path";
    } else if (k === "--help" || k === "-h") {
      args.mode = "help";
    } else if (k === "--version" || k === "-v") {
      args.mode = "version";
    }
  }
  return args;
}

function loadPrompt() {
  if (!existsSync(PROMPT_PATH)) {
    throw new Error(`prompt file not found: ${PROMPT_PATH}`);
  }
  return readFileSync(PROMPT_PATH, "utf-8");
}

function extractPromptSection(full) {
  const lines = full.split("\n");
  const startIdx = lines.findIndex((l) => l.trim() === "## Prompt");
  if (startIdx === -1) return full;
  const body = lines.slice(startIdx + 1);
  const endIdx = body.findIndex((l) => /^##\s+/.test(l));
  const section = endIdx === -1 ? body : body.slice(0, endIdx);
  return section.join("\n").trim() + "\n";
}

function loadVersion() {
  try {
    const pkg = JSON.parse(readFileSync(resolve(PKG_ROOT, "package.json"), "utf-8"));
    return pkg.version || "0.0.0";
  } catch {
    return "0.0.0";
  }
}

function printHelp() {
  console.log(`simplicio-prompt v${loadVersion()}

Tuple-Space + Yool execution prompt for coding agents.

Usage:
  simplicio-prompt                       Print full prompt to stdout
  simplicio-prompt --raw                 Print only the Prompt section
  simplicio-prompt --install [FILE]      Install into target file (default: CLAUDE.md)
  simplicio-prompt --path                Print absolute path of the prompt file
  simplicio-prompt --version             Print version
  simplicio-prompt --help                Show this help

Examples:
  npx simplicio-prompt --install CLAUDE.md
  npx simplicio-prompt --install AGENTS.md
  npx simplicio-prompt --install .cursorrules
  npx simplicio-prompt --raw > my-prompt.md
`);
}

function installInto(targetPath, content) {
  const block = `${MARK_START}\n${content.trim()}\n${MARK_END}\n`;
  if (!existsSync(targetPath)) {
    writeFileSync(targetPath, block);
    console.error(`# wrote ${targetPath}`);
    return;
  }
  const existing = readFileSync(targetPath, "utf-8");
  if (existing.includes(MARK_START) && existing.includes(MARK_END)) {
    const before = existing.slice(0, existing.indexOf(MARK_START));
    const afterStart = existing.indexOf(MARK_END) + MARK_END.length;
    const after = existing.slice(afterStart);
    const updated = `${before}${block.trim()}${after}`;
    writeFileSync(targetPath, updated);
    console.error(`# updated ${targetPath} (replaced existing simplicio-prompt block)`);
    return;
  }
  const sep = existing.endsWith("\n") ? "\n" : "\n\n";
  appendFileSync(targetPath, `${sep}${block}`);
  console.error(`# appended simplicio-prompt block to ${targetPath}`);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.mode === "help") return printHelp();
  if (args.mode === "version") return console.log(loadVersion());
  if (args.mode === "path") return console.log(PROMPT_PATH);

  const full = loadPrompt();
  const content = args.raw ? extractPromptSection(full) : full;

  if (args.mode === "print") {
    process.stdout.write(content);
    return;
  }
  if (args.mode === "install") {
    const target = resolve(process.cwd(), args.target || "CLAUDE.md");
    installInto(target, args.raw ? content : extractPromptSection(full));
    return;
  }
}

try {
  main();
} catch (e) {
  console.error(`simplicio-prompt: ${e.message}`);
  process.exit(1);
}
