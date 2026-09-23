import os
import tempfile
import pytest

# 必须在导入 app.* 之前指定临时数据库目录（app.config 在导入时读取 DATA_DIR）
_TMP_DATA_DIR = tempfile.mkdtemp(prefix="paintcan-test-")
os.environ.setdefault("DATA_DIR", _TMP_DATA_DIR)


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c
