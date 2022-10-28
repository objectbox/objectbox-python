# Copyright 2019-2021 ObjectBox Ltd. All rights reserved.
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


class Version:
    def __init__(self, major: int, minor: int, patch: int, label: str = ""):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.label = label

    def __str__(self):
        result = ".".join(map(str, [self.major, self.minor, self.patch]))
        if len(self.label) > 0:
            result += "-" + self.label
        return result
