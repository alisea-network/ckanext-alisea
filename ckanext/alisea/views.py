"""Resource view helpers for ALiSEA website resources."""

from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import urlparse

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

WEBSITE_FORMATS = frozenset({"website", "webpage"})
WEBSITE_VIEW_TYPE = "alisea_website_view"
LEGACY_WEBPAGE_VIEW_TYPE = "webpage_view"


def is_website_resource(resource: dict[str, Any]) -> bool:
    """True when the resource is an external site (ALiSEA Website/Webpage format)."""
    fmt = (resource.get("format") or "").strip().lower()
    return fmt in WEBSITE_FORMATS and bool(resource.get("url"))


def get_website_target_url(
    resource: dict[str, Any],
    resource_view: Optional[dict[str, Any]] = None,
) -> str:
    """Return the external URL to redirect to."""
    if resource_view:
        page_url = (resource_view.get("page_url") or "").strip()
        if page_url:
            return page_url
    return (resource.get("url") or "").strip()


def _is_safe_redirect_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _remove_legacy_webpage_views(context, resource_id: str, existing_views: list) -> None:
    """Remove old webpage_view iframe views created before the redirect view existed."""
    for view in existing_views:
        if view["view_type"] != LEGACY_WEBPAGE_VIEW_TYPE:
            continue
        try:
            toolkit.get_action("resource_view_delete")(
                {**context, "defer_commit": True},
                {"id": view["id"]},
            )
        except (toolkit.ObjectNotFound, toolkit.NotAuthorized) as err:
            log.warning(
                "Could not remove legacy webpage_view %s: %s",
                view["id"],
                err,
            )


def create_website_view_if_needed(context, resource):
    """Create an alisea_website_view redirect for one resource when applicable."""
    if not is_website_resource(resource):
        return

    resource_id = resource.get("id")
    if not resource_id:
        return

    target_url = get_website_target_url(resource)
    if not _is_safe_redirect_url(target_url):
        log.warning(
            "Skipping website view for resource %s: invalid URL %r",
            resource_id,
            target_url,
        )
        return

    existing_views = toolkit.get_action("resource_view_list")(
        context, {"id": resource_id}
    )
    if any(v["view_type"] == WEBSITE_VIEW_TYPE for v in existing_views):
        _remove_legacy_webpage_views(context, resource_id, existing_views)
        return

    _remove_legacy_webpage_views(context, resource_id, existing_views)

    view = {
        "resource_id": resource_id,
        "view_type": WEBSITE_VIEW_TYPE,
        "title": toolkit._("Website"),
        "page_url": target_url,
    }
    try:
        toolkit.get_action("resource_view_create")(
            {**context, "defer_commit": True},
            view,
        )
    except toolkit.ValidationError as err:
        log.warning(
            "Could not create %s for resource %s: %s",
            WEBSITE_VIEW_TYPE,
            resource_id,
            err,
        )
    except toolkit.NotAuthorized:
        log.warning(
            "Not authorized to create %s for resource %s",
            WEBSITE_VIEW_TYPE,
            resource_id,
        )


def add_website_resource_views(context, data_dict):
    """Create redirect views for resources with Website/Webpage format."""
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
        create_website_view_if_needed(context, resource)

    return data_dict
