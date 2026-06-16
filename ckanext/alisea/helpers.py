from ckan.plugins import toolkit as tk
from ckan.lib.helpers import url_for_static_or_external
import logging
from ckan.common import _, request, config


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
