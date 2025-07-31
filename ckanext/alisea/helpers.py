from ckan.plugins import toolkit as tk
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
