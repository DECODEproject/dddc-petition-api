import pytest
from starlette.testclient import TestClient

from app.main import api
from app.model import Base, engine


@pytest.fixture(scope="session", autouse=True)
def client(request):
    def fn():
        Base.metadata.drop_all(bind=engine)

    request.addfinalizer(fn)
    return TestClient(api)
