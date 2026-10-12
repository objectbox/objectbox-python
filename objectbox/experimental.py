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

# Marshalling objects (put): None (the generic flatbuffers.Builder), FAST_BUILDER or CODEGEN; at most one is active
FAST_BUILDER = "fast builder"
CODEGEN = "codegen"
_flatbuffers_mode = None
_flatbuffers_verify = False


def _set_flatbuffers_mode(mode: str, enabled: bool, verify: bool):
    global _flatbuffers_mode, _flatbuffers_verify
    if enabled:
        _flatbuffers_mode = mode
        _flatbuffers_verify = verify
    elif _flatbuffers_mode == mode:
        _flatbuffers_mode = None
        _flatbuffers_verify = False


def enable_fast_flatbuffers_builder(enabled: bool = True, verify: bool = False):
    """Experimental: marshals objects (put) with a FlatBuffers builder that is precomputed per entity instead of the
    generic flatbuffers.Builder; this is much faster, especially for many objects. It produces the same bytes.
    Applies to all entities in this process, from the next put on.
    Only one experimental builder is active: enabling this one replaces enable_flatbuffers_codegen();
    disabling it (enabled=False) has no effect if the other one is active.

    :param verify: additionally marshals each object with the generic builder and raises an AssertionError if the
        bytes differ (slower than the generic builder alone; for testing).
    """
    _set_flatbuffers_mode(FAST_BUILDER, enabled, verify)


def is_fast_flatbuffers_builder_enabled() -> bool:
    return _flatbuffers_mode == FAST_BUILDER


def enable_flatbuffers_codegen(enabled: bool = True, verify: bool = False):
    """Experimental: like enable_fast_flatbuffers_builder(), but additionally generates Python code per entity
    (compiled once, at the entity's first put or read) that marshals its objects; this is faster than the fast builder.
    It produces the same bytes as the generic flatbuffers.Builder.
    Reading objects (get, queries) also uses generated code, which returns the same objects as the default
    (flatbuffers.Table), but is much faster, especially for entities with many properties.
    Only one experimental builder is active: enabling this one replaces enable_fast_flatbuffers_builder();
    disabling it (enabled=False) has no effect if the other one is active.

    :param verify: see enable_fast_flatbuffers_builder(); for reading, each object is additionally read with
        flatbuffers.Table and an AssertionError is raised if any property value differs.
    """
    _set_flatbuffers_mode(CODEGEN, enabled, verify)


def is_flatbuffers_codegen_enabled() -> bool:
    return _flatbuffers_mode == CODEGEN
