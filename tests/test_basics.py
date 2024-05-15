#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import objectbox
from tests.common import load_empty_test_default_store


def test_version():
    assert objectbox.version.major == 0  # update for major version changes
    assert objectbox.version.minor >= 6

    assert objectbox.version_core.major == 4  # update for major version changes
    assert objectbox.version_core.minor >= 0

    info = objectbox.version_info()
    print("\nVersion found:", info)
    assert len(info) > 10
    assert str(objectbox.version) in info
    assert str(objectbox.version_core) in info


def test_open():
    load_empty_test_default_store()
