import os
import time
import subprocess
import socket
import typing
import platform
import glob
import zipfile
import tarfile
import signal
import urllib.request

import pytest
import objectbox
from objectbox.logger import logger
from tests.model import *
import numpy as np
from datetime import datetime, timezone
from objectbox import *
import logging

from dataclasses import dataclass

test_logger = logging.getLogger(__name__)


def remove_json_model_file():
    path = os.path.dirname(os.path.realpath(__file__))
    json_file = os.path.join(path, "objectbox-model.json")
    if os.path.exists(json_file):
        os.remove(json_file)


def create_default_model():
    model = Model()
    model.entity(TestEntity)
    model.entity(TestEntityDatetime)
    model.entity(TestEntityFlex)
    model.entity(VectorEntity)
    return model


def create_test_store(db_path: str = "testdata", clear_db: bool = True) -> objectbox.Store:
    """ Creates a Store instance with all entities. """

    is_inmemory = db_path.startswith("memory:")
    logger.info(f"DB path: {db_path} ({'in-memory' if is_inmemory else ''})")

    if clear_db:
        Store.remove_db_files(db_path)
        remove_json_model_file()
    return objectbox.Store(model=create_default_model(), directory=db_path)


@dataclass
class SyncServerConfig:
    pid: int
    port: int


def _get_sync_server_job_name() -> str:
    """Returns the GitLab CI job name for downloading the sync server based on OS and architecture."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "b:mac-arm64-server"
        else:
            return "b:mac-x64-server"
    elif system == "linux":
        if machine in ("arm64", "aarch64"):
            return "b:linux-aarch64-server"
        else:
            return "b:linux-x64-server"
    else:
        raise RuntimeError(f"Unsupported platform: {system} {machine}")


def start_sync_server() -> typing.Union[SyncServerConfig, None]:
    """ Downloads and starts the ObjectBox Sync Server binary. """
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # Check for required environment variables
    ci_server_url = os.environ.get("CI_SERVER_URL")
    ci_job_token = os.environ.get("CI_JOB_TOKEN")

    if not ci_server_url or not ci_job_token:
        test_logger.warning("CI_SERVER_URL or CI_JOB_TOKEN not set, cannot download sync server")
        return None

    try:
        # GitLab artifact download configuration
        project_id = "4"
        job_name = _get_sync_server_job_name()
        branch = "syncdev"

        # URL-encode the job name (colon -> %3A)
        job_name_encoded = job_name.replace(":", "%3A")

        artifact_url = f"{ci_server_url}/api/v4/projects/{project_id}/jobs/artifacts/{branch}/download?job={job_name_encoded}"

        print(f"Downloading sync-server artifact from: {artifact_url}")

        # Download the artifact
        artifact_path = os.path.join(current_dir, "artifact.zip")
        request = urllib.request.Request(artifact_url, headers={"JOB-TOKEN": ci_job_token})
        with urllib.request.urlopen(request) as response, open(artifact_path, "wb") as out_file:
            out_file.write(response.read())

        # Extract the outer artifact zip
        with zipfile.ZipFile(artifact_path, "r") as zip_ref:
            zip_ref.extractall(current_dir)

        # Find and extract the sync-server archive (could be .zip or .tar.gz)
        artifacts_dir = os.path.join(current_dir, "artifacts")

        # Look for both .zip and .tar.gz files
        sync_server_zips = glob.glob(os.path.join(artifacts_dir, "objectbox-sync-server-*.zip"))
        sync_server_tarballs = glob.glob(os.path.join(artifacts_dir, "objectbox-sync-server-*.tar.gz"))

        if sync_server_zips:
            sync_server_archive = sync_server_zips[0]
            print(f"Found sync-server zip archive: {sync_server_archive}")
            with zipfile.ZipFile(sync_server_archive, "r") as zip_ref:
                zip_ref.extractall(current_dir)
        elif sync_server_tarballs:
            sync_server_archive = sync_server_tarballs[0]
            print(f"Found sync-server tar.gz archive: {sync_server_archive}")
            with tarfile.open(sync_server_archive, "r:gz") as tar_ref:
                tar_ref.extractall(current_dir)
        else:
            raise RuntimeError("Could not find objectbox-sync-server-*.zip or *.tar.gz in artifacts")

        # Verify sync-server executable exists
        sync_server_executable = os.path.join(current_dir, "sync-server")
        if platform.system().lower() == "windows":
            sync_server_executable += ".exe"

        if not os.path.exists(sync_server_executable):
            raise RuntimeError("sync-server executable not found after extraction")

        # Make executable on Unix systems
        if os.name != "nt":
            os.chmod(sync_server_executable, 0o755)

        print("Starting sync-server in background...")

        # Run sync-server in background
        process = subprocess.Popen(
            [
                sync_server_executable,
                "--model", os.path.join(current_dir, "objectbox-model.json"),
                "--unsecured-no-authentication",
                "--debug"
            ],
            cwd=current_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print(f"Sync server started with PID: {process.pid}")

        # Wait for server to be ready
        time.sleep(2)

        # Check if server is still running
        if process.poll() is not None:
            raise RuntimeError("Sync server failed to start")

        # Wait for port to be available
        start_time = time.time()
        while (time.time() - start_time) < 10:
            try:
                with socket.create_connection(("127.0.0.1", 9999), timeout=1):
                    break
            except (OSError, socket.timeout):
                time.sleep(0.5)
        else:
            raise RuntimeError("Timed out waiting for Sync Server to start")

        print("Sync server is running")
        return SyncServerConfig(pid=process.pid, port=9999)

    except Exception as e:
        test_logger.warning(f"Could not start ObjectBox Sync Server: {e}")
        return None


def stop_sync_server(pid: int):
    """ Stops the ObjectBox Sync Server process. """
    try:
        print(f"Stopping sync server (PID: {pid})...")

        # Send SIGTERM (or equivalent on Windows)
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
        else:
            os.kill(pid, signal.SIGTERM)

        # Wait for process to stop
        for i in range(10):
            try:
                os.kill(pid, 0)  # Check if process exists
                time.sleep(1)
            except OSError:
                print(f"Sync server stopped after {i + 1}s")
                return

        # Force kill if still running
        print("Sync server still running after 10s, sending SIGKILL...")
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
        else:
            os.kill(pid, signal.SIGKILL)

        print("Stopped ObjectBox Sync Server")
    except Exception as e:
        test_logger.warning(f"Could not stop ObjectBox Sync Server: {e}")


def assert_equal_prop(actual, expected, default):
    if isinstance(expected, objectbox.model.properties.Property):
        assert (actual == default)
    else:
        assert (actual == expected)


def assert_equal_prop_vector(actual, expected, default):
    assert (actual == np.array(expected)).all() or (isinstance(
        expected, objectbox.model.Property) and actual == default)


# compare approx values
def assert_equal_prop_approx(actual, expected, default):
    if isinstance(expected, objectbox.model.properties.Property):
        assert (actual == default)
    else:
        assert (pytest.approx(actual) == expected)


def assert_equal(actual: TestEntity, expected: TestEntity):
    """Check that two TestEntity objects have the same property data"""
    assert actual.id == expected.id
    assert_equal_prop(actual.int64, expected.int64, 0)
    assert_equal_prop(actual.int32, expected.int32, 0)
    assert_equal_prop(actual.int16, expected.int16, 0)
    assert_equal_prop(actual.int8, expected.int8, 0)
    assert_equal_prop(actual.float64, expected.float64, 0)
    assert_equal_prop(actual.float32, expected.float32, 0)
    assert_equal_prop(actual.bytes, expected.bytes, b'')
    assert_equal_prop_vector(actual.bools, expected.bools, np.array([]))
    assert_equal_prop_vector(actual.ints, expected.ints, np.array([]))
    assert_equal_prop_vector(actual.shorts, expected.shorts, np.array([]))
    assert_equal_prop_vector(actual.chars, expected.chars, np.array([]))
    assert_equal_prop_vector(actual.longs, expected.longs, np.array([]))
    assert_equal_prop_vector(actual.floats, expected.floats, np.array([]))
    assert_equal_prop_vector(actual.doubles, expected.doubles, np.array([]))
    assert_equal_prop_approx(actual.bools_list, expected.bools_list, [])
    assert_equal_prop_approx(actual.ints_list, expected.ints_list, [])
    assert_equal_prop_approx(actual.shorts_list, expected.shorts_list, [])
    assert_equal_prop_approx(actual.chars_list, expected.chars_list, [])
    assert_equal_prop_approx(actual.longs_list, expected.longs_list, [])
    assert_equal_prop_approx(actual.floats_list, expected.floats_list, [])
    assert_equal_prop_approx(actual.doubles_list, expected.doubles_list, [])
    assert_equal_prop_approx(actual.date, expected.date, datetime.fromtimestamp(0, timezone.utc))
    assert_equal_prop(actual.date_nano, expected.date_nano, 0)
    assert_equal_prop(actual.flex, expected.flex, None)
