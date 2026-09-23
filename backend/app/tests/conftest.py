import os
import tempfile

# 测试使用独立的临时数据目录，必须在导入 app.* 之前设置
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="paintcan-test-"))

import pytest

@pytest.fixture
def svc():
    from app import seed
    from app.db import DB_PATH
    if DB_PATH.exists():
        DB_PATH.unlink()
    seed.init_db()
    from app.services.paint_service import PaintService
    with PaintService() as s:
        yield s
