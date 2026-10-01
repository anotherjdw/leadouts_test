"""Shared pytest fixtures: a local Spark session and one temporary folder per test run."""

import os
import re
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

# Set before any SparkSession starts. SPARK_LOCAL_IP stops Spark binding to a network
# interface it cannot reach (common on laptops and VPNs); PYSPARK_PYTHON makes Spark's
# Python workers use this interpreter, not whatever `python` is first on PATH.
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
os.environ["PYSPARK_PYTHON"] = sys.executable


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """A local SparkSession shared by every test, without Hive, as in Glue."""
    return (
        SparkSession.builder.master("local[*]")
        .appName("leadouts_test-tests")
        .config("spark.pyspark.python", sys.executable)
        .getOrCreate()
    )


@pytest.fixture(scope="session")
def fixture_root() -> Iterator[Path]:
    """One temporary folder for every file the test run writes, deleted at the end."""
    with tempfile.TemporaryDirectory() as root:
        yield Path(root)


@pytest.fixture
def test_dir(fixture_root: Path, request: pytest.FixtureRequest) -> Path:
    """A fresh folder under `fixture_root` for one test, named from the test id."""
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", request.node.nodeid)
    path = fixture_root / name
    path.mkdir()
    return path
