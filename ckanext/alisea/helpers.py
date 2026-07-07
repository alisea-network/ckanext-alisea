from ckan.plugins import toolkit as tk
from ckan.lib.helpers import url_for_static_or_external
import json
import logging
from ckan.common import _, request, config

FLAG_BASE_URL = (
    'https://kh.ali-sea.org/wp-content/themes/alisea-wordpress-theme/assets/flags/'
)

LANGUAGE_TO_FLAG = {
    'English': ('en', 'gb.png', 'English'),
    'Khmer': ('km', 'kh.png', 'Khmer'),
    'Lao': ('lo', 'la.png', 'Lao'),
    'Myanmar': ('my_MM', 'mm.png', 'Myanmar'),
    'Vietnamese': ('vi', 'vn.png', 'Vietnamese'),
}

log = logging.getLogger(__name__)


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


def _pkg_get(package, key, default=None):
    """Read a field from CKAN package dicts or dict-like search results."""
    if package is None:
        return default
    getter = getattr(package, 'get', None)
    if callable(getter):
        try:
            value = getter(key)
            if value is not None:
                return value
        except (AttributeError, KeyError, TypeError):
            pass
    try:
        return package[key]
    except (KeyError, TypeError):
        pass
    return getattr(package, key, default)


def _action_context():
    import ckan.model as model
    return {
        'model': model,
        'session': model.Session,
        'ignore_auth': True,
    }


def _package_has_language(package):
    return bool(_normalize_language_list(_pkg_get(package, 'language')))


def enrich_packages_language_from_db(packages, context=None):
    """
    Fill missing language on search results.

    package_search reads validated_data_dict from Solr, which may not include
    language on older indexes even though the facet field is populated.
    """
    if not packages:
        return

    missing = [pkg for pkg in packages if not _package_has_language(pkg)]
    if not missing:
        return

    import ckan.model as model

    if context is None:
        context = _action_context()

    missing_ids = [pkg['id'] for pkg in missing if pkg.get('id')]
    if missing_ids:
        extras = (
            model.Session.query(model.PackageExtra)
            .filter(
                model.PackageExtra.package_id.in_(missing_ids),
                model.PackageExtra.key == 'language',
            )
            .all()
        )
        languages_by_id = {
            extra.package_id: _normalize_language_list(extra.value)
            for extra in extras
        }
        for pkg in missing:
            pkg_id = pkg.get('id')
            if pkg_id in languages_by_id:
                pkg['language'] = languages_by_id[pkg_id]

    still_missing = [pkg for pkg in packages if not _package_has_language(pkg)]
    for pkg in still_missing:
        pkg_id = pkg.get('id') or pkg.get('name')
        if not pkg_id:
            continue
        try:
            full = tk.get_action('package_show')(context, {'id': pkg_id})
            language = full.get('language')
            if language:
                pkg['language'] = language
        except Exception as exc:
            log.warning(
                'Could not load language for %s: %s', pkg_id, exc
            )


def _flags_from_languages(raw):
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


def _normalize_flags(flags):
    """Accept only a list of flag dicts from cache/search results."""
    if not flags:
        return []
    if isinstance(flags, str):
        try:
            flags = json.loads(flags)
        except (ValueError, TypeError):
            return []
    if not isinstance(flags, list):
        return []
    return [
        item for item in flags
        if isinstance(item, dict) and item.get('url') and item.get('label')
    ]


def _language_raw_from_package(package):
    """Read language value from a package dict (search or show)."""
    raw = _pkg_get(package, 'language')
    if raw is not None:
        return raw

    extras = _pkg_get(package, 'extras') or []
    if isinstance(extras, list):
        for extra in extras:
            if isinstance(extra, dict) and extra.get('key') == 'language':
                return extra.get('value')
    return None


def get_dataset_language_flags(package):
    """
    Return flag dicts for dataset Language metadata (Additional Info).
    Each item: {code, url, label}.
    """
    try:
        for key in ('alisea_language_flags', '_language_flags'):
            cached = _normalize_flags(_pkg_get(package, key))
            if cached:
                return cached

        raw = _language_raw_from_package(package)
        if not _normalize_language_list(raw):
            pkg_id = _pkg_get(package, 'id') or _pkg_get(package, 'name')
            if pkg_id:
                try:
                    full = tk.get_action('package_show')(
                        _action_context(),
                        {'id': pkg_id},
                    )
                    raw = _language_raw_from_package(full)
                except Exception as exc:
                    log.warning(
                        'Could not load language for %s: %s', pkg_id, exc
                    )

        return _flags_from_languages(raw)
    except Exception as exc:
        log.warning('get_dataset_language_flags failed: %s', exc)
        return []


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
