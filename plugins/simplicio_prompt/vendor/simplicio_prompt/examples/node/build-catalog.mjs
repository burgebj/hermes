#!/usr/bin/env node
/**
 * Node wrapper around scripts/build_hamt.py.
 * Lets JS/TS adopters consume the same catalog format.
 *
 * Usage:
 *   node examples/node/build-catalog.mjs --source AGENTS.md --output .catalog/hamt.json
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { existsSync, readFileSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..", "..");
const PY_SCRIPT = resolve(REPO_ROOT, "scripts", "build_hamt.py");

function parseArgs(argv) {
  const args = { format: "auto" };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === "--source") args.source = argv[++i];
    else if (k === "--output") args.output = argv[++i];
    else if (k === "--format") args.format = argv[++i];
    else if (k === "--help" || k === "-h") {
      console.log("Usage: build-catalog.mjs --source <path> --output <path> [--format auto|agents-md|yool-list]");
      process.exit(0);
    }
  }
  if (!args.source || !args.output) {
    console.error("error: --source and --output are required");
    process.exit(2);
  }
  return args;
}

function runPython(args) {
  return new Promise((resolveP, rejectP) => {
    if (!existsSync(PY_SCRIPT)) {
      rejectP(new Error(`build_hamt.py not found at ${PY_SCRIPT}`));
      return;
    }
    const py = process.env.PYTHON || "python3";
    const child = spawn(py, [
      PY_SCRIPT,
      "--source", args.source,
      "--output", args.output,
      "--format", args.format,
    ], { stdio: ["ignore", "inherit", "inherit"] });
    child.on("error", rejectP);
    child.on("exit", (code) => {
      if (code === 0) resolveP();
      else rejectP(new Error(`build_hamt.py exited with code ${code}`));
    });
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  await runPython(args);
  if (existsSync(args.output)) {
    const catalog = JSON.parse(readFileSync(args.output, "utf-8"));
    console.error(`# loaded catalog: ${catalog.meta?.count} entries`);
  }
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
