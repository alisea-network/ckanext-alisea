"""ALiSEA resource view: redirect to external website (no iframe)."""

from __future__ import annotations

from typing import Any

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.alisea.views import WEBSITE_VIEW_TYPE, get_website_target_url, is_website_resource


class AliseaWebsiteViewMixin:
    """IResourceView mixin for the Alisea plugin."""

    def info(self) -> dict[str, Any]:
        ignore_empty = toolkit.get_validator("ignore_empty")
        unicode_safe = toolkit.get_validator("unicode_safe")
        return {
            "name": WEBSITE_VIEW_TYPE,
            "title": toolkit._("Website"),
            "icon": "link",
            "iframed": True,
            "always_available": False,
            "default_title": toolkit._("Website"),
            "schema": {"page_url": [ignore_empty, unicode_safe]},
        }

    def can_view(self, data_dict: dict[str, Any]) -> bool:
        return is_website_resource(data_dict["resource"])

    def view_template(self, context, data_dict: dict[str, Any]) -> str:
        return "alisea_website_redirect_view.html"

    def form_template(self, context, data_dict: dict[str, Any]) -> str:
        return "alisea_website_redirect_form.html"

    def setup_template_variables(self, context, data_dict: dict[str, Any]) -> dict[str, Any]:
        return {
            "target_url": get_website_target_url(
                data_dict["resource"],
                data_dict.get("resource_view"),
            ),
        }
