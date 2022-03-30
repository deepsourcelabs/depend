"""Test Postgres functions"""
import pytest

from db.postgres_worker import add_data, upd_data, get_data
from handle_env import get_db


@pytest.fixture
def psql():
    """
    Returns DB connection if available
    """
    return get_db()


@pytest.fixture(autouse=True)
def skip_by_status(request, psql):
    """
    Skips tests if Postgres not available
    :param request: pytest request
    :param psql: database object
    """
    if request.node.get_closest_marker('skip_status') and \
            request.node.get_closest_marker('skip_status').args[0] == psql:
        pytest.skip('Skipped as Postgres connection status: {}'.format(psql))


@pytest.mark.skip_status(None)
def test_run_db(psql):
    """
    Add data into test DB
    """
    add_data(
        psql,
        "MURDOCK_TEST",
        "test",
        "murdock",
        "0.0.1",
        "murdock",
        ["1.0"],
        ["MIT"],
        {},
        ["a;v", "b;v"],
        True
    )
    data = get_data(
        psql,
        "MURDOCK_TEST",
        "test",
        "murdock",
        "0.0.1"
    )
    assert data[0]["PKG_LIC"] == "GPL"


@pytest.mark.skip_status(None)
def test_check_db(psql):
    """
    Checks if added data exists in DB
    """
    upd_data(
        psql,
        "MURDOCK_TEST",
        "test",
        "murdock",
        "0.0.1",
        "murdock",
        ["1.0"],
        ["GPL"],
        {},
        ["a;v", "b;v"]
    )
    data = get_data(
        psql,
        "MURDOCK_TEST",
        "test",
        "murdock",
        "0.0.1"
    )
    assert data[0]["PKG_LIC"] == "GPL"
