interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  // add other environment variables if needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
