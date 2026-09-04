/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base da API (ex.: /api/v1 ou http://host:5000/api/v1). */
  readonly VITE_API_URL?: string;
  /** @deprecated Use VITE_API_URL */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
