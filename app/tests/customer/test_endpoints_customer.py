from fastapi.testclient import TestClient
from fastapi import status

from app.util import cap_logger
from app.main import app

test_client = TestClient(app=app)


def test_read_customer():
    response = test_client.get('/customer/3078')
    cap_logger.info(response)
    assert response.status_code == 200
