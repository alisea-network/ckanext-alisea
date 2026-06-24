from ckan.plugins import toolkit as tk
from ckan.lib.helpers import url_for_static_or_external
import json
import logging
from ckan.common import _, request, config

FLAG_BASE_URL = (
    'https://kh.ali-sea.org/wp-content/themes/alisea-wordpress-theme/assets/flags/'
)

# CKAN "Language" field values (multiple_select) → flag asset
LANGUAGE_TO_FLAG = {
    'English': ('en', 'gb.png', 'English'),
    'Khmer': ('km', 'kh.png', 'Khmer'),
    'Lao': ('lo', 'la.png', 'Lao'),
    'Myanmar': ('my_MM', 'mm.png', 'Myanmar'),
    'Vietnamese': ('vi', 'vn.png', 'Vietnamese'),
}


def get_google_tag():
    gtag = tk.config.get('ckan.alisea.gtag')
    return gtag


def convert_to_list(value):
    return value.split(',') if isinstance(value, str) else value


def lao_current_url() -> str:
    ''' Returns Lao language url'''
    ckan_site_url = config.get('ckan.site_url')
    current_url = request.environ['CKAN_CURRENT_URL']
    full_lao_url = ckan_site_url + "/lo" + current_url
    return full_lao_url


def _normalize_language_list(value):
    """Parse dataset language field (list, JSON string, or comma-separated)."""
    if value is None or value == '':
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if v]
        except (ValueError, TypeError):
            pass
        if ',' in value:
            return [v.strip() for v in value.split(',') if v.strip()]
        return [value.strip()] if value.strip() else []
    return []


def get_dataset_language_flags(package):
    """
    Return flag dicts for dataset Language metadata (Additional Info).
    Each item: {code, url, label}.
    """
    if isinstance(package, dict):
        raw = package.get('language')
    else:
        raw = getattr(package, 'language', None)

    flags = []
    seen = set()
    for lang in _normalize_language_list(raw):
        mapping = LANGUAGE_TO_FLAG.get(lang)
        if not mapping or lang in seen:
            continue
        seen.add(lang)
        code, filename, label = mapping
        flags.append({
            'code': code,
            'url': FLAG_BASE_URL + filename,
            'label': label,
        })
    return flags


def get_organization_structured_data():
    """Schema.org Organization JSON-LD for the CKAN homepage."""
    logo = tk.config.get('ckan.alisea.organization_logo')
    if not logo:
        site_logo = tk.config.get('ckan.site_logo')
        if site_logo:
            logo = url_for_static_or_external(site_logo)
    if not logo:
        logo = (
            'https://kh.ali-sea.org/wp-content/uploads/2024/09/'
            'cropped-alisea-side-logo-1.png'
        )

    site_url = tk.config.get('ckan.site_url', 'https://ckan.ali-sea.org').rstrip('/')

    return {
        '@context': 'https://schema.org',
        '@type': 'Organization',
        'name': tk.config.get('ckan.site_title', 'ALiSEA'),
        'url': site_url + '/',
        'logo': logo,
    }
