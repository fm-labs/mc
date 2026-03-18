export const MC_BRAND_NAME =
    import.meta.env.VITE_MC_BRAND_NAME || 'mission control'

export const MC_API_BASE_URL =
    import.meta.env.VITE_MC_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:${window.location.port}`

export const FEAT_SETTINGS_ENABLED =
    import.meta.env.VITE_FEAT_SETTINGS_ENABLED === 'true' || false

export const FEAT_TASKS_ENABLED =
    import.meta.env.VITE_FEAT_TASKS_ENABLED === 'true' || false

export const FEAT_TOOLS_ENABLED =
    import.meta.env.VITE_FEAT_TOOLS_ENABLED === 'true' || false

export const FEAT_APP_TEMPLATES_ENABLED =
    import.meta.env.VITE_FEAT_APP_TEMPLATES_ENABLED === 'true' || false


export const PORTAINER_TEMPLATE_URLS = [
    {
        format: 'portainer',
        label: 'Official Portainer Templates (v3)',
        url: 'https://raw.githubusercontent.com/portainer/templates/refs/heads/v3/templates.json',
    },
    {
        format: 'portainer',
        label: 'Official Portainer Templates (v2)',
        url: 'https://raw.githubusercontent.com/portainer/templates/refs/heads/master/templates-2.0.json',
    },
    {
        format: 'portainer',
        label: 'Portainer Templates by Lissy93 (v2)',
        url: 'https://raw.githubusercontent.com/Lissy93/portainer-templates/refs/heads/main/templates.json',
    },
]
