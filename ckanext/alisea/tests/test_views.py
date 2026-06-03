"""Tests for website resource view helpers."""

import pytest

from ckanext.alisea.views import is_website_resource


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
