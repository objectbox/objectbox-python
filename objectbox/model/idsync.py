import random
from typing import *
from objectbox.logger import logger
from objectbox.model import Model
from objectbox.model.entity import _Entity
from objectbox.model.properties import Property, Index, HnswIndex
from objectbox.model.iduid import IdUid

MODEL_PARSER_VERSION = 5


class IdSync:
    def __init__(self, model: Model, model_json_filepath: str):
        self.model = model

        self.model_filepath = model_json_filepath
        self.model_json = None
        self._load_model_json()

    def _load_model_json(self):
        import json
        from os import path

        if not path.exists(self.model_filepath):
            logger.debug(f"Model file not found: {self.model_filepath}")
            return

        with open(self.model_filepath, "rt") as model_file:
            self.model_json = json.load(model_file)
        logger.debug(f"Syncing model with model file: {self.model_filepath}")

    def _save_model_json(self):
        """ Replaces model JSON with the serialized model whose ID/UIDs are assigned. """

        # model.validate_ids_assigned()

        model_json = {
            "_note1": "KEEP THIS FILE! Check it into a version control system (VCS) like git.",
            "_note2": "ObjectBox manages crucial IDs for your object model. See docs for details.",
            "_note3": "If you have VCS merge conflicts, you must resolve them according to ObjectBox docs.",
            "modelVersionParserMinimum": MODEL_PARSER_VERSION,
            "entities": [],
            "lastEntityId": str(self.model.last_entity_iduid),
            "lastIndexId": str(self.model.last_index_iduid)
        }
        # TODO lastRelationId
        # TODO modelVersion
        # TODO retiredEntityUids
        # TODO retiredIndexUids
        # TODO retiredPropertyUids
        # TODO retiredRelationUids
        # TODO version

        for entity in self.model.entities:
            entity_json = {
                "id": str(entity.iduid),
                "name": entity.name,
                "lastPropertyId": str(entity.last_property_iduid),
                "properties": []
            }
            for prop in entity.properties:
                prop_json = {
                    "id": str(prop.iduid),
                    "name": prop.name,
                    "type": prop._ob_type,
                    "flags": prop._flags
                }
                if prop.index is not None:
                    prop_json["indexId"] = str(prop.index.iduid)
                entity_json["properties"].append(prop_json)
            model_json["entities"].append(entity_json)

        import json
        with open(self.model_filepath, "w") as model_file:
            model_file.write(json.dumps(model_json, indent=2))  # Pretty

    # *** Sync ***

    def _find_entity_json_by_name(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """ Finds the entity data by name in the model JSON file. """
        if self.model_json is None:
            return None
        for entity_json in self.model_json["entities"]:
            if entity_json["name"] == entity_name:
                return entity_json
        return None

    def _find_property_json_by_name(self, entity_name: str, prop_name: str) -> Optional[Dict[str, Any]]:
        """ Finds the entity property data by name in the model JSON file. """
        entity_json = self._find_entity_json_by_name(entity_name)
        if entity_json is None:
            return None
        for prop_json in entity_json["properties"]:
            if prop_json["name"] == prop_name:
                return prop_json
        return None

    @staticmethod
    def _generate_uid() -> int:
        return random.getrandbits(63) + 1  # 0 would be invalid

    def _validate_uid_unassigned(self, uid: int):
        """ Validates that the UID is not assigned for any other entity/property/index. """
        pass  # TODO

    def _sync_index_id(self, entity: _Entity, prop: Property, index: Union[Index, HnswIndex]) -> None:
        """ Given an index, syncs its ID/UID with the JSON file. """
        iduid_json = None
        prop_json = self._find_property_json_by_name(entity.name, prop.name)
        if prop_json is not None and "indexId" in prop_json:
            iduid_json = IdUid.from_str(prop_json["indexId"])
        if iduid_json is None:  # Index not present in JSON
            if index.has_uid():
                self._validate_uid_unassigned(index.uid)
            else:
                gen_uid = self._generate_uid()
                index.iduid.uid = gen_uid
            index.iduid = IdUid(self.model.last_index_iduid.id + 1, index.uid)
        else:  # Index present in JSON
            if index.has_uid() and index.uid != iduid_json.uid:
                self._validate_uid_unassigned(index.uid)
                index.iduid = IdUid(self.model.last_index_iduid.id + 1, index.uid)  # Assign ID
            else:  # not index.has_uid() or index.uid != iduid_json.uid
                index.iduid = iduid_json

    def _validate_matching_prop(self, entity: _Entity, prop: Property, prop_json: Dict[str, Any]):
        """ Validates that the given property matches the JSON property. """
        assert prop.name == prop_json["name"], \
            f"Property {entity.name}.{prop.name} mismatches property found in JSON file " \
            f"(name {prop.name} != type {prop_json['name']})"  # Shouldn't happen (JSON property is got by name)
        assert prop._ob_type == prop_json["type"], \
            f"Property {entity.name}.{prop.name} mismatches property found in JSON file " \
            f"(type {prop._ob_type} != type {prop_json['type']})"
        assert prop._flags == prop_json["flags"], \
            f"Property {entity.name}.{prop.name} mismatches property found in JSON file " \
            f"(flags {prop._flags} != type {prop_json['flags']})"

    def _sync_property_id(self, entity: _Entity, prop: Property) -> None:
        """ Given an entity's property, syncs its ID/UID with the JSON file. """
        prop_json = self._find_property_json_by_name(entity.name, prop.name)
        if prop_json is None:  # Property not present in JSON
            if prop.has_uid():
                self._validate_uid_unassigned(prop.uid)
            else:
                prop.iduid.uid = self._generate_uid()
            prop.iduid = IdUid(entity.last_property_iduid.id + 1, prop.uid)  # Assign ID
        else:  # Property present in JSON
            iduid_json = IdUid.from_str(prop_json["id"])
            if prop.has_uid() and prop.uid != iduid_json.uid:  # New property
                self._validate_uid_unassigned(prop.uid)
                prop.iduid = IdUid(entity.last_property_iduid.id + 1, prop.uid)  # Assign ID
            else:  # not prop.has_uid() or prop.uid == iduid_json.uid
                self._validate_matching_prop(entity, prop, prop_json)
                prop.iduid = iduid_json

    def _validate_matching_entity(self, entity: _Entity, entity_json: Dict[str, Any]):
        """ Validates that the given entity matches the JSON entity. """
        assert entity.name == entity_json["name"], \
            f"Entity {entity.name} mismatches property found in JSON file " \
            f"(name {entity.name} != type {entity_json['name']})"  # Shouldn't happen (JSON entity is got by name)
        assert len(entity.properties) == len(entity_json["properties"]), \
            f"Entity {entity.name} mismatches entity found in JSON file " \
            f"({len(entity.properties)} properties != {len(entity_json['properties'])} properties)"
        # TODO check relations count
        pass  # TODO check properties' fields?

    def _sync_entity_id(self, entity: _Entity) -> None:
        """ Given an entity, syncs its ID/UID with the JSON file. """
        entity_json = self._find_entity_json_by_name(entity.name)
        if entity_json is None:  # Entity not present in JSON file
            if entity.has_uid():
                self._validate_uid_unassigned(entity.uid)
            else:
                entity.iduid.uid = self._generate_uid()
            entity.iduid = IdUid(self.model.last_entity_iduid.id + 1, entity.uid)  # Assign ID
        else:  # Entity present in JSON file
            iduid_json = IdUid.from_str(entity_json["id"])
            if entity.has_uid() and entity.uid != iduid_json.uid:  # New entity
                self._validate_uid_unassigned(entity.uid)
                entity.iduid = IdUid(self.model.last_entity_iduid.id + 1, entity.uid)  # Assign ID
            else:  # not entity.has_uid() or entity.uid == iduid_json.uid
                self._validate_matching_entity(entity, entity_json)
                entity.iduid = iduid_json

    def sync(self):
        """ Syncs the provided model with the model JSON file. """

        # Sync entities ID/UID
        if self.model_json is not None:
            self.model.last_entity_iduid = IdUid.from_str(self.model_json["lastEntityId"])
        else:
            self.model.last_entity_iduid = IdUid(0, 0)
        for entity in self.model.entities:
            self._sync_entity_id(entity)
            if entity.id > self.model.last_entity_iduid.id:  # If assignment occurred, update last_entity_iduid
                self.model.last_entity_iduid = entity.iduid

        # Sync properties ID/UID
        for entity in self.model.entities:
            entity_json = self._find_entity_json_by_name(entity.name)
            if entity_json is not None:
                entity.last_property_iduid = IdUid.from_str(entity_json["lastPropertyId"])
            else:
                entity.last_property_iduid = IdUid(0, 0)
            for prop in entity.properties:
                self._sync_property_id(entity, prop)
                if prop.id > entity.last_property_iduid.id:  # If assignment occurred, update last_property_iduid
                    entity.last_property_iduid = prop.iduid

        # Sync indexes ID/UID
        if self.model_json is not None:
            self.model.last_index_iduid = IdUid.from_str(self.model_json["lastIndexId"])
        else:
            self.model.last_index_iduid = IdUid(0, 0)
        for entity in self.model.entities:
            for prop in entity.properties:
                if prop.index is not None:
                    index = prop.index
                    self._sync_index_id(entity, prop, index)
                    if index.id > self.model.last_index_iduid.id:  # If assignment occurred, update last_index_iduid
                        self.model.last_index_iduid = index.iduid

        # TODO Sync relations ID/UID(s)

        self._save_model_json()


def sync_model(model: Model, model_filepath: str = "obx-model.json"):
    """ Syncs the provided model with the model JSON file. """

    id_sync = IdSync(model, model_filepath)
    id_sync.sync()
