"""Resource view helpers for ALiSEA website resources."""

from __future__ import annotations

import logging
from typing import Any

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

WEBSITE_FORMATS = frozenset({"website", "webpage"})
WEBPAGE_VIEW_TYPE = "webpage_view"


def is_website_resource(resource: dict[str, Any]) -> bool:
    """True when the resource is an external site (ALiSEA Website/Webpage format)."""
    fmt = (resource.get("format") or "").strip().lower()
    return fmt in WEBSITE_FORMATS and bool(resource.get("url"))


def patch_webpage_view_can_view() -> None:
    """Extend CKAN webpage_view so Website/Webpage formats are previewable."""
    try:
        from ckanext.webpageview.plugin import WebPageView
    except ImportError:
        log.warning(
            "ckanext.webpageview not loaded; enable webpage_view in ckan.plugins"
        )
        return

    if getattr(WebPageView.can_view, "_alisea_patched", False):
        return

    original_can_view = WebPageView.can_view

    def can_view(self, data_dict):
        if is_website_resource(data_dict["resource"]):
            return True
        return original_can_view(self, data_dict)

    can_view._alisea_patched = True
    WebPageView.can_view = can_view


def create_webpage_view_if_needed(context, resource):
    """Create a webpage_view for one resource when applicable."""
    if not is_website_resource(resource):
        return

    resource_id = resource.get("id")
    if not resource_id:
        return

    existing_views = toolkit.get_action("resource_view_list")(
        context, {"id": resource_id}
    )
    if any(v["view_type"] == WEBPAGE_VIEW_TYPE for v in existing_views):
        return

    view = {
        "resource_id": resource_id,
        "view_type": WEBPAGE_VIEW_TYPE,
        "title": toolkit._("Website"),
    }
    try:
        toolkit.get_action("resource_view_create")(
            {**context, "defer_commit": True},
            view,
        )
    except toolkit.ValidationError as err:
        log.warning(
            "Could not create webpage_view for resource %s: %s",
            resource_id,
            err,
        )
    except toolkit.NotAuthorized:
        log.warning(
            "Not authorized to create webpage_view for resource %s",
            resource_id,
        )


def add_website_resource_views(context, data_dict):
    """Create webpage_view for resources with Website/Webpage format."""
    package_id = data_dict.get("id")
    if not package_id:
        return data_dict

    try:
        package = toolkit.get_action("package_show")(
            {**context, "include_tracking": False},
            {"id": package_id},
        )
    except toolkit.ObjectNotFound:
        return data_dict

    for resource in package.get("resources", []):
        create_webpage_view_if_needed(context, resource)

    return data_dict
