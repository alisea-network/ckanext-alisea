"""Tests for website resource view helpers."""

import pytest

from ckanext.alisea.views import (
    get_website_target_url,
    is_video_resource,
    is_website_resource,
)


@pytest.mark.parametrize(
    "resource,expected",
    [
        ({"format": "Website", "url": "https://example.org"}, True),
        ({"format": "webpage", "url": "https://example.org/page"}, True),
        ({"format": "PDF", "url": "https://example.org/doc.pdf"}, False),
        ({"format": "Website", "url": ""}, False),
        ({"format": "HTML", "url": "https://example.org"}, False),
    ],
)
def test_is_website_resource(resource, expected):
    assert is_website_resource(resource) is expected


def test_get_website_target_url_prefers_view_page_url():
    resource = {"url": "https://example.org/resource"}
    resource_view = {"page_url": "https://example.org/override"}
    assert get_website_target_url(resource, resource_view) == "https://example.org/override"


@pytest.mark.parametrize(
    "resource,expected",
    [
        ({"format": "MP4", "url": "https://example.org/video.mp4"}, True),
        ({"format": "mp4", "url": "https://example.org/video.mp4"}, True),
        ({"format": "PDF", "url": "https://example.org/doc.pdf"}, False),
        ({"format": "MP4", "url": ""}, False),
    ],
)
def test_is_video_resource(resource, expected):
    assert is_video_resource(resource) is expected


def test_get_website_target_url_falls_back_to_resource_url():
    resource = {"url": "https://example.org/resource"}
    assert get_website_target_url(resource) == "https://example.org/resource"
