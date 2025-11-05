export const MC_BRAND_NAME =
  import.meta.env.VITE_MC_BRAND_NAME || 'mission control'

// export const MC_API_BASE_URL =
//   import.meta.env.VITE_MC_API_BASE_URL || 'http://127.0.0.1:13080/'

export const FEAT_DOMAIN_WEBCHECK_ENABLED =
  import.meta.env.VITE_FEAT_DOMAIN_WEBCHECK_ENABLED === 'true' || false

export const FEAT_DOMAIN_VIEWS_ENABLED =
  import.meta.env.VITE_FEAT_DOMAIN_VIEWS_ENABLED === 'true' || false

export const FEAT_SETTINGS_ENABLED =
  import.meta.env.VITE_FEAT_SETTINGS_ENABLED === 'true' || false

export const FEAT_TASKS_ENABLED =
  import.meta.env.VITE_FEAT_TASKS_ENABLED === 'true' || false

export const FEAT_ANSIBLE_ENABLED =
  import.meta.env.VITE_FEAT_ANSIBLE_ENABLED === 'true' || false

export const FEAT_TOOLS_ENABLED =
  import.meta.env.VITE_FEAT_TOOLS_ENABLED === 'true' || false

export const FEAT_INTEGRATIONS_ENABLED =
  import.meta.env.VITE_FEAT_INTEGRATIONS_ENABLED === 'true' || false

/**
 * @deprecated
 */
export const WEBCHECK_API_BASE_URL =
  import.meta.env.VITE_WEBCHECK_API_BASE_URL || 'http://127.0.0.1:13080/api/xscan/webcheck'
