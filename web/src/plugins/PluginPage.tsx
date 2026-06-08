import { Component, type ReactNode, useSyncExternalStore } from "react";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import {
  getPluginComponent,
  getPluginLoadError,
  onPluginRegistered,
} from "./registry";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";
import type { Translations } from "@/i18n/types";

/** Renders a plugin tab once its bundle has called `register()`. */
export function PluginPage({ name }: { name: string }) {
  const { t } = useI18n();
  // Subscribe in render (via useSyncExternalStore) so we never miss
  // `register()` if the script loads before a useEffect would run.
  const Component = useSyncExternalStore(
    (onChange) => onPluginRegistered(onChange),
    () => getPluginComponent(name) ?? null,
    () => null,
  );
  const loadError = useSyncExternalStore(
    (onChange) => onPluginRegistered(onChange),
    () => getPluginLoadError(name) ?? null,
    () => null,
  );

  if (Component) {
    // A plugin bundle compiled against a newer SDK (e.g. calling
    // SDK.authedFetch / SDK.buildWsUrl) throws while rendering when the host
    // web bundle is stale and lacks those helpers. Without a boundary that
    // throw unmounts the whole dashboard. Contain it to this tab instead.
    return (
      <PluginErrorBoundary key={name} name={name} message={t.common.pluginCrashed}>
        <Component />
      </PluginErrorBoundary>
    );
  }

  if (loadError) {
    return <PluginNotice message={formatPluginError(loadError, t)} />;
  }

  return (
    <div
      className={cn(
        "flex items-center gap-2 p-4",
        "font-mondwest text-sm tracking-[0.1em] text-text-tertiary",
      )}
    >
      <Spinner className="shrink-0" />
      <span>{t.common.loading}</span>
    </div>
  );
}

function PluginNotice({ message }: { message: string }) {
  return (
    <div
      className={cn(
        "max-w-lg p-4",
        "font-mondwest text-sm tracking-[0.08em] text-text-secondary",
      )}
      role="alert"
    >
      {message}
    </div>
  );
}

class PluginErrorBoundary extends Component<
  { name: string; message: string; children: ReactNode },
  { crashed: boolean }
> {
  state = { crashed: false };

  static getDerivedStateFromError() {
    return { crashed: true };
  }

  componentDidCatch(error: unknown) {
    console.warn(
      `[plugins] "${this.props.name}" crashed while rendering. If you recently updated Hermes, rebuild the web assets (run "npm run build" in web/).`,
      error,
    );
  }

  render() {
    if (this.state.crashed) {
      return <PluginNotice message={this.props.message} />;
    }
    return this.props.children;
  }
}

function formatPluginError(code: string, t: Translations): string {
  if (code === "LOAD_FAILED") return t.common.pluginLoadFailed;
  if (code === "NO_REGISTER") return t.common.pluginNotRegistered;
  return code;
}
