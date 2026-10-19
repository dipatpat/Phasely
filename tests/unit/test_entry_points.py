import subprocess
import sys

import pytest


@pytest.mark.parametrize("entry_point", ["app.main", "app.celery"])
def test_entry_point_loads_every_model(entry_point):
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import {entry_point}; "
            "from sqlalchemy.orm import configure_mappers; configure_mappers()",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
