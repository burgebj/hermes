import { useEffect } from 'react'
import { useStore } from '@nanostores/react'
import { atom } from 'nanostores'

/**
 * Per-workspace git-repo detection for the sidebar.
 *
 * The "new session in a worktree" fork icon must only appear for workspace
 * groups whose path is a real git repository. We probe each distinct path once
 * via the `git.is_repo` gateway method and memoize the answer for the lifetime
 * of the renderer — a workspace doesn't stop being a repo while the app is open,
 * and re-probing on every sidebar render would be wasteful.
 *
 * Results live in a module-level nanostore so every sidebar instance shares one
 * cache and re-renders when a probe resolves.
 */

// path -> isRepo. Absence means "not yet probed".
const $repoByPath = atom<Record<string, boolean>>({})

// Paths with an in-flight or completed probe, so we never probe the same path
// twice (even before the first result lands).
const probed = new Set<string>()

type RequestGateway = <T = unknown>(method: string, params?: Record<string, unknown>) => Promise<T>

async function probePath(path: string, requestGateway: RequestGateway): Promise<void> {
  try {
    const res = await requestGateway<{ is_repo?: boolean }>('git.is_repo', { cwd: path })
    $repoByPath.set({ ...$repoByPath.get(), [path]: Boolean(res?.is_repo) })
  } catch {
    // Treat a failed probe as "not a repo" — the icon simply won't appear, and
    // the backend would fall back gracefully anyway if it somehow got asked.
    $repoByPath.set({ ...$repoByPath.get(), [path]: false })
  }
}

/**
 * Probe every supplied workspace path for git-repo-ness (once each) and return
 * a `Set` of the paths that are repos. Re-renders when probes resolve.
 *
 * @param paths Distinct, non-null workspace paths to probe.
 * @param requestGateway Gateway RPC caller.
 */
export function useWorkspaceGitRepos(paths: string[], requestGateway: RequestGateway): Set<string> {
  const repoByPath = useStore($repoByPath)

  useEffect(() => {
    for (const path of paths) {
      if (!path || probed.has(path)) {
        continue
      }
      probed.add(path)
      void probePath(path, requestGateway)
    }
  }, [paths, requestGateway])

  const repos = new Set<string>()
  for (const [path, isRepo] of Object.entries(repoByPath)) {
    if (isRepo) {
      repos.add(path)
    }
  }
  return repos
}
