import { useCallback, useRef, useState, type DragEvent as ReactDragEvent } from 'react'
import { type NodeApi, type NodeRendererProps, Tree, type TreeApi } from 'react-arborist'

import { PageLoader } from '@/components/page-loader'
import { Button } from '@/components/ui/button'
import { Codicon } from '@/components/ui/codicon'
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger
} from '@/components/ui/context-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useResizeObserver } from '@/hooks/use-resize-observer'
import { useI18n } from '@/i18n'
import { cn } from '@/lib/utils'
import { notify, notifyError } from '@/store/notifications'

import type { TreeNode } from './use-project-tree'

const ROW_HEIGHT = 22
const INDENT = 10

// Paths may be POSIX (remote) or Windows (local); split on either separator.
function parentDirOf(p: string): string {
  const idx = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\'))

  return idx > 0 ? p.slice(0, idx) : p
}

function baseNameOf(p: string): string {
  const idx = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\'))

  return idx >= 0 ? p.slice(idx + 1) : p
}

// Always join with '/'. Node's fs accepts forward slashes on Windows, and the
// remote host is POSIX, so this is safe for both execution targets.
function joinPath(dir: string, name: string): string {
  return `${dir.replace(/[/\\]+$/, '')}/${name}`
}

type FsAction =
  | { dir: string; kind: 'newFile'; name: string }
  | { dir: string; kind: 'newFolder'; name: string }
  | { dir: string; kind: 'rename'; name: string; targetPath: string }
  | { dir: string; kind: 'delete'; name: string; targetPath: string }

const DIALOG_COPY: Record<FsAction['kind'], { title: string; label: string; confirm: string }> = {
  newFile: { title: 'New file', label: 'File name', confirm: 'Create' },
  newFolder: { title: 'New folder', label: 'Folder name', confirm: 'Create' },
  rename: { title: 'Rename', label: 'New name', confirm: 'Rename' },
  delete: { title: 'Delete', label: '', confirm: 'Delete' }
}

interface ProjectTreeProps {
  collapseNonce: number
  cwd: string
  data: TreeNode[]
  onActivateFile: (path: string) => void
  onActivateFolder: (path: string) => void
  onLoadChildren: (id: string) => void | Promise<void>
  onNodeOpenChange: (id: string, open: boolean) => void
  onPreviewFile?: (path: string) => void
  onRefreshDir?: (dirPath: string) => void | Promise<void>
  openState: Record<string, boolean>
}

export function ProjectTree({
  collapseNonce,
  cwd,
  data,
  onActivateFile,
  onActivateFolder,
  onLoadChildren,
  onNodeOpenChange,
  onPreviewFile,
  onRefreshDir,
  openState
}: ProjectTreeProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const treeRef = useRef<TreeApi<TreeNode> | null>(null)
  const [size, setSize] = useState({ height: 0, width: 0 })
  const [action, setAction] = useState<FsAction | null>(null)
  const [actionName, setActionName] = useState('')
  const [busy, setBusy] = useState(false)
  const [dropActive, setDropActive] = useState(false)

  const canMutate = Boolean(window.hermesDesktop?.mkdir)

  const syncTreeSize = useCallback(() => {
    const el = containerRef.current

    if (!el) {
      return
    }

    const { height, width } = el.getBoundingClientRect()

    setSize(prev => (prev.height === height && prev.width === width ? prev : { height, width }))
  }, [])

  useResizeObserver(syncTreeSize, containerRef)

  const handleToggle = useCallback(
    (id: string) => {
      const node = treeRef.current?.get(id)

      if (!node) {
        return
      }

      onNodeOpenChange(id, node.isOpen)

      if (node.isOpen && node.data?.isDirectory && node.data.children === undefined) {
        void onLoadChildren(id)
      }
    },
    [onLoadChildren, onNodeOpenChange]
  )

  const handleActivate = useCallback(
    (node: NodeApi<TreeNode>) => {
      if (node.data && !node.data.isDirectory) {
        onPreviewFile?.(node.data.id)
      }
    },
    [onPreviewFile]
  )

  const openAction = useCallback((next: FsAction) => {
    setAction(next)
    setActionName(next.kind === 'rename' ? next.name : '')
  }, [])

  const runAction = useCallback(async () => {
    if (!action) {
      return
    }

    const desktop = window.hermesDesktop
    const trimmed = actionName.trim()

    if (action.kind !== 'delete' && !trimmed) {
      return
    }

    setBusy(true)

    try {
      let result: { ok: boolean; error?: string } | undefined

      if (action.kind === 'newFolder') {
        result = await desktop?.mkdir?.(joinPath(action.dir, trimmed))
      } else if (action.kind === 'newFile') {
        result = await desktop?.newFile?.(joinPath(action.dir, trimmed))
      } else if (action.kind === 'rename') {
        result = await desktop?.renamePath?.(action.targetPath, joinPath(action.dir, trimmed))
      } else {
        result = await desktop?.deletePath?.(action.targetPath)
      }

      if (result && !result.ok) {
        throw new Error(result.error || 'Operation failed')
      }

      await onRefreshDir?.(action.dir)
      notify({ kind: 'success', title: `${DIALOG_COPY[action.kind].title} done`, message: trimmed || action.name })
      setAction(null)
    } catch (error) {
      notifyError(error, `${DIALOG_COPY[action.kind].title} failed`)
    } finally {
      setBusy(false)
    }
  }, [action, actionName, onRefreshDir])

  // Drag-drop upload: dropping OS files onto the tree copies/SCP-uploads them
  // into the current working directory, then refreshes it (#38464).
  const handleDrop = useCallback(
    async (event: ReactDragEvent<HTMLDivElement>) => {
      const files = Array.from(event.dataTransfer?.files ?? [])

      if (files.length === 0 || !cwd) {
        return
      }

      // OS file drop — handle it here, don't let the chat composer also catch it.
      event.preventDefault()
      event.stopPropagation()
      setDropActive(false)

      const getPath = window.hermesDesktop?.getPathForFile
      const upload = window.hermesDesktop?.uploadFile

      if (!getPath || !upload) {
        return
      }

      const localPaths = files.map(file => getPath(file)).filter(Boolean)

      if (localPaths.length === 0) {
        return
      }

      setBusy(true)

      try {
        const results = await Promise.all(localPaths.map(localPath => upload(localPath, cwd)))
        const failed = results.filter(r => !r?.ok).length

        await onRefreshDir?.(cwd)

        if (failed > 0) {
          notify({ kind: 'warning', title: `Uploaded ${results.length - failed}/${results.length}`, message: `${failed} failed` })
        } else {
          notify({
            kind: 'success',
            title: `Uploaded ${results.length} file${results.length === 1 ? '' : 's'}`,
            message: cwd
          })
        }
      } catch (error) {
        notifyError(error, 'Upload failed')
      } finally {
        setBusy(false)
      }
    },
    [cwd, onRefreshDir]
  )

  const handleDragOver = useCallback((event: ReactDragEvent<HTMLDivElement>) => {
    if (Array.from(event.dataTransfer?.types ?? []).includes('Files')) {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'copy'
      setDropActive(true)
    }
  }, [])

  return (
    <div
      className={cn('relative min-h-0 flex-1 overflow-hidden', dropActive && 'ring-1 ring-inset ring-primary/60')}
      onDragLeave={() => setDropActive(false)}
      onDragOver={canMutate ? handleDragOver : undefined}
      onDrop={canMutate ? event => void handleDrop(event) : undefined}
      ref={containerRef}
    >
      {size.height > 0 && size.width > 0 ? (
        <Tree<TreeNode>
          childrenAccessor={node => (node?.isDirectory ? (node.children ?? []) : null)}
          data={data}
          disableDrag
          disableDrop
          disableEdit
          height={size.height}
          indent={INDENT}
          initialOpenState={openState}
          key={`${cwd}:${collapseNonce}`}
          onActivate={handleActivate}
          onToggle={handleToggle}
          openByDefault={false}
          padding={0}
          ref={treeRef}
          rowHeight={ROW_HEIGHT}
          width={size.width}
        >
          {props => (
            <ProjectTreeRow
              {...props}
              canMutate={canMutate}
              onAttachFile={onActivateFile}
              onAttachFolder={onActivateFolder}
              onPreviewFile={onPreviewFile}
              onRequestAction={openAction}
            />
          )}
        </Tree>
      ) : (
        <TreeSizingState />
      )}

      <Dialog open={action !== null} onOpenChange={open => (open ? undefined : setAction(null))}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{action ? DIALOG_COPY[action.kind].title : ''}</DialogTitle>
            {action?.kind === 'delete' ? (
              <DialogDescription>Delete “{action.name}”? This cannot be undone.</DialogDescription>
            ) : null}
          </DialogHeader>

          {action && action.kind !== 'delete' ? (
            <Input
              autoFocus
              onChange={event => setActionName(event.target.value)}
              onKeyDown={event => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  void runAction()
                }
              }}
              placeholder={DIALOG_COPY[action.kind].label}
              value={actionName}
            />
          ) : null}

          <DialogFooter>
            <Button disabled={busy} onClick={() => setAction(null)} size="sm" variant="text">
              Cancel
            </Button>
            <Button
              disabled={busy || (action?.kind !== 'delete' && !actionName.trim())}
              onClick={() => void runAction()}
              size="sm"
              variant={action?.kind === 'delete' ? 'destructive' : 'default'}
            >
              {action ? DIALOG_COPY[action.kind].confirm : ''}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function TreeSizingState() {
  const { t } = useI18n()

  return <PageLoader aria-label={t.rightSidebar.loadingFiles} className="min-h-24 px-3" />
}

function ProjectTreeRow({
  canMutate,
  dragHandle,
  node,
  onAttachFile,
  onAttachFolder,
  onPreviewFile,
  onRequestAction,
  style
}: NodeRendererProps<TreeNode> & {
  canMutate: boolean
  onAttachFile: (path: string) => void
  onAttachFolder: (path: string) => void
  onPreviewFile?: (path: string) => void
  onRequestAction: (action: FsAction) => void
}) {
  if (!node.data) {
    return <div style={style} />
  }

  const isFolder = node.data.isDirectory
  const isPlaceholder = node.data.id.endsWith('::__loading__')
  const path = node.data.id
  // New items land inside a folder; for a file, they land alongside it.
  const targetDir = isFolder ? path : parentDirOf(path)

  const row = (
    <div
      aria-expanded={isFolder ? node.isOpen : undefined}
      aria-selected={node.isSelected}
      className={cn(
        'group/row flex h-full cursor-pointer select-none items-center gap-1 border border-transparent px-3 text-xs font-normal leading-(--file-tree-row-height) text-(--ui-text-secondary) transition-colors hover:bg-(--ui-row-hover-background) hover:text-foreground',
        node.isSelected && 'bg-(--ui-row-active-background) text-foreground',
        isPlaceholder && 'pointer-events-none italic text-muted-foreground/70'
      )}
      draggable={!isPlaceholder}
      onClick={event => {
        event.stopPropagation()

        if (isPlaceholder) {
          return
        }

        if (event.shiftKey) {
          ;(isFolder ? onAttachFolder : onAttachFile)(node.data.id)

          return
        }

        if (isFolder) {
          node.toggle()
        } else {
          node.select()
        }
      }}
      onDoubleClick={event => {
        event.stopPropagation()

        if (!isFolder && !isPlaceholder) {
          onPreviewFile?.(node.data.id)
        }
      }}
      onDragStart={event => {
        if (isPlaceholder) {
          event.preventDefault()

          return
        }

        const payload = JSON.stringify([{ isDirectory: isFolder, path: node.data.id }])

        event.dataTransfer.effectAllowed = 'copy'
        event.dataTransfer.setData('application/x-hermes-paths', payload)
        event.dataTransfer.setData('text/plain', node.data.id)
      }}
      ref={dragHandle}
      style={style}
    >
      {isFolder && !isPlaceholder && (
        <span aria-hidden className="flex w-3 items-center justify-center">
          <Codicon
            className="text-(--ui-text-tertiary)"
            name={node.isOpen ? 'chevron-down' : 'chevron-right'}
            size="0.75rem"
          />
        </span>
      )}
      {!isFolder && <span aria-hidden className="w-3 shrink-0" />}
      <span aria-hidden className="flex w-3.5 items-center justify-center text-(--ui-text-tertiary)">
        {isPlaceholder ? (
          <Codicon name="loading" size="0.75rem" spinning />
        ) : isFolder ? (
          <Codicon name={node.isOpen ? 'folder-opened' : 'folder'} size="0.875rem" />
        ) : (
          <Codicon name="file" size="0.875rem" />
        )}
      </span>
      <span className="min-w-0 flex-1 truncate">{node.data.name}</span>
    </div>
  )

  if (!canMutate || isPlaceholder) {
    return row
  }

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>{row}</ContextMenuTrigger>
      <ContextMenuContent className="w-44">
        <ContextMenuItem onSelect={() => onRequestAction({ kind: 'newFile', dir: targetDir, name: '' })}>
          New file…
        </ContextMenuItem>
        <ContextMenuItem onSelect={() => onRequestAction({ kind: 'newFolder', dir: targetDir, name: '' })}>
          New folder…
        </ContextMenuItem>
        <ContextMenuSeparator />
        <ContextMenuItem
          onSelect={() =>
            onRequestAction({ kind: 'rename', dir: parentDirOf(path), name: baseNameOf(path), targetPath: path })
          }
        >
          Rename…
        </ContextMenuItem>
        <ContextMenuItem
          className="text-destructive focus:text-destructive"
          onSelect={() =>
            onRequestAction({ kind: 'delete', dir: parentDirOf(path), name: baseNameOf(path), targetPath: path })
          }
        >
          Delete
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  )
}
