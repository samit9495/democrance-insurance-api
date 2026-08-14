"""Phase 10: the OpenAPI surface and the single-file demo client all render."""

import pytest

pytestmark = pytest.mark.django_db


def test_schema_generates_without_warnings(tmp_path):
    from django.core.management import call_command

    out = tmp_path / "schema.yml"
    # --fail-on-warn turns any spectacular warning into a non-zero exit / raise.
    call_command("spectacular", file=str(out), validate=True, fail_on_warn=True)
    assert out.exists()


def test_schema_endpoint_serves_openapi(anon_client):
    response = anon_client.get("/api/v1/schema/")

    assert response.status_code == 200
    assert b"openapi" in response.content


@pytest.mark.parametrize("path", ["/api/v1/docs/", "/api/v1/redoc/"])
def test_interactive_docs_render(anon_client, path):
    assert anon_client.get(path).status_code == 200


def test_demo_spa_is_served_at_the_root(anon_client):
    response = anon_client.get("/")

    assert response.status_code == 200
    assert b"Democrance Insurance API" in response.content
