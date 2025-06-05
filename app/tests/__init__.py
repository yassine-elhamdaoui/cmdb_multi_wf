from fastapi.testclient import TestClient

import app

print("Initializing the Test objects")

client = TestClient(app=app)


