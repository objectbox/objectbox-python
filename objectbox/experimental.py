# Copyright 2026 ObjectBox Ltd. All rights reserved.
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

"""Experimental features: off by default; they may change or be removed in any release."""

_fast_flatbuffers_builder = False
_fast_flatbuffers_builder_verify = False


def enable_fast_flatbuffers_builder(enabled: bool = True, verify: bool = False):
    """Experimental: marshals objects (put) with a FlatBuffers builder that is precomputed per entity instead of the
    generic flatbuffers.Builder; this is much faster, especially for many objects. It produces the same bytes.
    Applies to all entities in this process, from the next put on.

    :param verify: additionally marshals each object with the generic builder and raises an AssertionError if the
        bytes differ (slower than the generic builder alone; for testing).
    """
    global _fast_flatbuffers_builder, _fast_flatbuffers_builder_verify
    _fast_flatbuffers_builder = enabled
    _fast_flatbuffers_builder_verify = enabled and verify


def is_fast_flatbuffers_builder_enabled() -> bool:
    return _fast_flatbuffers_builder
