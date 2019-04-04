import pytest
from starlette.testclient import TestClient

from app.main import api
from app.model import Base, engine
from app.utils.helpers import debug

AAID = "aa_test_2"


def pytest_addoption(parser):
    parser.addoption(
        "--with-integration-test",
        action="store_true",
        default=False,
        help="Run the integration tests, after changing values on test_integration.py by hand",
    )


@pytest.fixture(scope="session", autouse=True)
def client(request):
    def fn():
        Base.metadata.drop_all(bind=engine)
        debug("FINISH")

    request.addfinalizer(fn)
    return TestClient(api)
