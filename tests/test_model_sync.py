import pytest

import objectbox.store
from objectbox import Entity, Id, Int64, Model, Store, String
from objectbox.store_options import StoreOptions


@Entity(model="model-sync-test")
class SyncTestNote:
    id = Id
    text = String


@Entity()
class SyncTestOther:
    id = Id
    value = Int64


@pytest.fixture
def sync_calls(monkeypatch):
    """Counts model JSON syncs (calls of sync_model by Store)."""
    calls = []
    original = objectbox.store.sync_model

    def counting_sync_model(model, model_filepath):
        calls.append(model_filepath)
        return original(model, model_filepath)

    monkeypatch.setattr(objectbox.store, "sync_model", counting_sync_model)
    return calls


@pytest.fixture
def model_passed_to_c(monkeypatch):
    """Counts how often a model is passed to the store options (and thus checked against the store's schema)."""
    calls = []
    original = StoreOptions.model

    def counting_model(self, model):
        calls.append(model)
        return original(self, model)

    monkeypatch.setattr(StoreOptions, "model", counting_model)
    return calls


def new_model() -> Model:
    model = Model()
    model.entity(SyncTestNote)
    return model


def test_model_synced_once(tmp_path, sync_calls):
    json_file = str(tmp_path / "objectbox-model.json")
    model = new_model()
    for i in range(3):
        store = Store(model=model, directory=str(tmp_path / f"db{i}"), model_json_file=json_file)
        store.box(SyncTestNote).put(SyncTestNote(text=f"store {i}"))
        store.close()
    assert len(sync_calls) == 1

    # A different model JSON file is synced
    other_json_file = str(tmp_path / "other-model.json")
    Store(model=model, directory=str(tmp_path / "db-other"), model_json_file=other_json_file).close()
    assert sync_calls[-1] == other_json_file

    # A changed model is synced again
    model.entity(SyncTestOther)
    Store(model=model, directory=str(tmp_path / "db-changed"), model_json_file=json_file).close()
    assert len(sync_calls) == 3


def test_model_name_synced_once(tmp_path, sync_calls):
    json_file = str(tmp_path / "objectbox-model.json")
    for i in range(3):
        store = Store(model="model-sync-test", directory=str(tmp_path / f"db{i}"), model_json_file=json_file)
        assert store.box(SyncTestNote).count() == 0
        store.close()
    assert len(sync_calls) == 1


def test_skip_model_sync(tmp_path, sync_calls, model_passed_to_c):
    json_file = str(tmp_path / "objectbox-model.json")
    model = new_model()
    db = str(tmp_path / "db")

    # New store: created with the model (also with skip_model_sync); the model JSON is synced once (IDs needed)
    store = Store(model=model, directory=db, model_json_file=json_file, skip_model_sync=True)
    store.box(SyncTestNote).put(SyncTestNote(text="hello"))
    store.close()
    assert len(sync_calls) == 1
    assert len(model_passed_to_c) == 1

    # Existing store: opened with the schema stored in the database, the model is not passed
    for _ in range(2):
        store = Store(model=model, directory=db, model_json_file=json_file, skip_model_sync=True)
        assert store.box(SyncTestNote).get(1).text == "hello"
        store.close()
    assert len(sync_calls) == 1
    assert len(model_passed_to_c) == 1

    # Without the option, the model is passed again (and checked against the schema)
    Store(model=model, directory=db, model_json_file=json_file).close()
    assert len(model_passed_to_c) == 2


def test_skip_model_sync_in_memory(sync_calls, model_passed_to_c, tmp_path):
    # In-memory stores are always created with the model
    store = Store(model=new_model(), directory="memory:skip-model-sync", model_json_file=str(tmp_path / "m.json"),
                  skip_model_sync=True)
    store.box(SyncTestNote).put(SyncTestNote(text="in memory"))
    store.close()
    assert len(model_passed_to_c) == 1
