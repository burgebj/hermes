/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_HERMES_GATEWAY_URL: string
  readonly VITE_HERMES_GATEWAY_TOKEN: string
  readonly VITE_STUDIO_PASSWORD: string
  readonly VITE_LINEAR_API_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
