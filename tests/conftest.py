import pytest
from objectbox.logger import logger
from common import *


# Fixtures in this file are used by all files in the same directory:
# https://docs.pytest.org/en/7.1.x/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files


def _clear_test_db():
    obx_remove_db_files(c_str(test_dir))


@pytest.fixture(autouse=True)
def cleanup_db():
    """ Fixture to ensure tests starts fresh and the DB is cleaned up on success/failure. """
    _clear_test_db()
    try:
        yield  # Run the test code
    finally:
        _clear_test_db()
