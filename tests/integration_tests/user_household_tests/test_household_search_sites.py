from fastapi.testclient import TestClient

from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


def test_get_search_sites_returns_empty_list(api_client: TestClient, unique_user: TestUser) -> None:
    response = api_client.get(api_routes.households_search_sites, headers=unique_user.token)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_search_site(api_client: TestClient, user_tuple: list[TestUser]) -> None:
    unique_user, other_user = user_tuple

    # grant permission
    user = other_user.repos.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = True
    other_user.repos.users.update(user.id, user)

    payload = {"name": "Test Blog", "domain": "testblog.com"}
    response = api_client.post(api_routes.households_search_sites, json=payload, headers=unique_user.token)
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "testblog.com"
    assert data["name"] == "Test Blog"
    assert data["enabled"] is True
    assert data["isBlocked"] is False
    assert "id" in data
    assert "householdId" in data


def test_create_search_site_no_permission(api_client: TestClient, user_tuple: list[TestUser]) -> None:
    unique_user, other_user = user_tuple

    user = other_user.repos.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = False
    other_user.repos.users.update(user.id, user)

    payload = {"name": "Blocked", "domain": "blocked.com"}
    response = api_client.post(api_routes.households_search_sites, json=payload, headers=unique_user.token)
    assert response.status_code == 403


def test_update_search_site(api_client: TestClient, user_tuple: list[TestUser]) -> None:
    unique_user, other_user = user_tuple

    user = other_user.repos.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = True
    other_user.repos.users.update(user.id, user)

    # Create a site to update
    payload = {"name": "Update Test", "domain": "updatetest.com"}
    create_resp = api_client.post(api_routes.households_search_sites, json=payload, headers=unique_user.token)
    assert create_resp.status_code == 201
    site_id = create_resp.json()["id"]

    # Update enabled flag
    update_url = f"{api_routes.households_search_sites}/{site_id}"
    update_resp = api_client.put(update_url, json={"enabled": False}, headers=unique_user.token)
    assert update_resp.status_code == 200
    assert update_resp.json()["enabled"] is False


def test_delete_search_site(api_client: TestClient, user_tuple: list[TestUser]) -> None:
    unique_user, other_user = user_tuple

    user = other_user.repos.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = True
    other_user.repos.users.update(user.id, user)

    # Create a site to delete
    payload = {"name": "Delete Test", "domain": "deletetest.com"}
    create_resp = api_client.post(api_routes.households_search_sites, json=payload, headers=unique_user.token)
    assert create_resp.status_code == 201
    site_id = create_resp.json()["id"]

    # Delete
    delete_url = f"{api_routes.households_search_sites}/{site_id}"
    delete_resp = api_client.delete(delete_url, headers=unique_user.token)
    assert delete_resp.status_code == 200
    assert "message" in delete_resp.json()

    # Verify it's gone
    get_resp = api_client.get(api_routes.households_search_sites, headers=unique_user.token)
    site_ids = [s["id"] for s in get_resp.json()]
    assert site_id not in site_ids


def test_restore_defaults(api_client: TestClient, user_tuple: list[TestUser]) -> None:
    """POST /restore-defaults must be reachable (not matched as a UUID)."""
    unique_user, other_user = user_tuple

    user = other_user.repos.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = True
    other_user.repos.users.update(user.id, user)

    # Add a custom site first
    payload = {"name": "Custom", "domain": "custom-site.com"}
    api_client.post(api_routes.households_search_sites, json=payload, headers=unique_user.token)

    # Restore defaults
    response = api_client.post(api_routes.households_search_sites_restore_defaults, headers=unique_user.token)
    assert response.status_code == 200
    defaults = response.json()
    assert len(defaults) == 7
    domains = {s["domain"] for s in defaults}
    assert "seriouseats.com" in domains
    assert "cooking.nytimes.com" in domains
    assert "custom-site.com" not in domains


def test_restore_defaults_no_permission(api_client: TestClient, user_tuple: list[TestUser]) -> None:
    unique_user, other_user = user_tuple

    user = other_user.repos.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = False
    other_user.repos.users.update(user.id, user)

    response = api_client.post(api_routes.households_search_sites_restore_defaults, headers=unique_user.token)
    assert response.status_code == 403


def test_search_sites_household_isolation(api_client: TestClient, h2_user: TestUser, unique_user: TestUser) -> None:
    """Sites created in one household must not appear in another."""
    # Enable manage permission for unique_user
    unique_user.repos.users.patch(unique_user.user_id, {"can_manage_household": True})

    payload = {"name": "Isolated", "domain": "isolated-household.com"}
    create_resp = api_client.post(api_routes.households_search_sites, json=payload, headers=unique_user.token)
    assert create_resp.status_code == 201

    # h2_user is in a different household
    other_resp = api_client.get(api_routes.households_search_sites, headers=h2_user.token)
    assert other_resp.status_code == 200
    other_domains = {s["domain"] for s in other_resp.json()}
    assert "isolated-household.com" not in other_domains
