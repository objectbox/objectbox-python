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

    def _find_entity_json_by_uid(self, uid: int) -> Optional[Dict[str, Any]]:
        """ Finds entity JSON by UID. """
        if self.model_json is None:
            return None
        for entity_json in self.model_json["entities"]:
            if IdUid.from_str(entity_json["id"]).uid == uid:
                return entity_json
        return None

    def _find_entity_json_by_name(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """ Finds entity JSON by name. """
        if self.model_json is None:
            return None
        for entity_json in self.model_json["entities"]:
            if entity_json["name"] == entity_name:
                return entity_json
        return None

    def _find_property_json_by_uid(self, entity_json: Dict[str, Any], uid: int) -> Optional[Dict[str, Any]]:
        """ Finds entity property JSON by property UID. """
        for prop_json in entity_json["properties"]:
            if IdUid.from_str(prop_json["id"]).uid == uid:
                return prop_json
        return None

    def _find_property_json_by_name(self, entity_json: Dict[str, Any], prop_name: str) -> Optional[Dict[str, Any]]:
        """ Finds entity property JSON by property name. """
        for prop_json in entity_json["properties"]:
            if prop_json["name"] == prop_name:
                return prop_json
        return None

    @staticmethod
    def _generate_uid() -> int:
        return random.getrandbits(63) + 1  # 0 would be invalid

    def _validate_uid_unassigned(self, uid: int):
        """ Validates that a user supplied UID is not assigned for any other entity/property/index.
        Raises a ValueError if the UID is already assigned elsewhere.
        """

        try:
            entity_json = self._find_entity_json_by_uid(uid)
            if entity_json is not None:
                raise ValueError(f"in Entity \"{entity_json['name']}\" ({entity_json['id']})")

            for entity_json in self.model_json["entities"]:
                prop_json = self._find_property_json_by_uid(entity_json, uid)
                if prop_json is not None:
                    raise ValueError(f"in Property \"{entity_json['name']}.{prop_json['name']}\" ({prop_json['id']})")
                for prop_json in entity_json["properties"]:
                    if "indexId" in prop_json and IdUid.from_str(prop_json["indexId"]).uid == uid:
                        raise ValueError(
                            f"in Property index \"{entity_json['name']}.{prop_json['name']}\" ({prop_json['id']})")
        except ValueError as error:
            raise ValueError(f"User supplied UID \"{uid}\" found {error}")

    def _validate_matching_prop(self, entity: _Entity, prop: Property, prop_json: Dict[str, Any]):
        """ Validates that the given property matches the JSON property. """
        try:
            # Don't check name equality as the property could be matched by UID (rename)
            # if validate_name and prop.name != prop_json["name"]:
            #    raise ValueError(f"name {prop.name} != name {prop_json['name']} (in JSON)")
            if prop._ob_type != prop_json["type"]:
                raise ValueError(f"OBX type {prop._ob_type} != OBX type {prop_json['type']} (in JSON)")
            elif prop._flags != prop_json["flags"]:
                raise ValueError(f"flags {prop._flags} != flags {prop_json['flags']} (in JSON)")
            elif prop.index is None and "indexId" in prop_json:
                raise ValueError("property hasn't index, but index found in JSON")
            elif prop.index is not None and "indexId" not in prop_json:
                raise ValueError("property has index, but index not found in JSON")
        except ValueError as error:
            raise ValueError(f"Property {entity.name}.{prop.name} mismatches property found in JSON file: {error}")

    def _load_or_assign_index(self, entity: _Entity, prop: Property, prop_json: Optional[Dict[str, Any]]):
        assert prop.index is not None
        index = prop.index

        # Fetch index ID/UID from JSON file
        iduid_json = None
        if (prop_json is not None) and ("indexId" in prop_json):
            iduid_json = IdUid.from_str(prop_json["indexId"])

        # User provided a UID not matching index's, make sure it's not assigned elsewhere
        if index.has_uid() and (iduid_json is not None) and (index.uid != iduid_json.uid):
            self._validate_uid_unassigned(index.uid)

        # Generate UID only if not supplied by the user, and index isn't found in JSON
        if not index.has_uid() and iduid_json is None:
            index.iduid.uid = self._generate_uid()

        if (iduid_json is not None) and (not index.has_uid() or index.iduid.uid == iduid_json.uid):  # Load
            index.iduid = IdUid.from_str(prop_json["indexId"])
        else:  # Assign
            index.iduid = IdUid(self.model.last_index_iduid.id + 1, index.uid)
            self.model.last_index_iduid = index.iduid

    def _load_or_assign_property(self, entity: _Entity, prop: Property, entity_json: Optional[Dict[str, Any]]):
        prop_json = None
        if prop.has_uid():
            if entity_json is not None:
                prop_json = self._find_property_json_by_uid(entity_json, prop.uid)
            if prop_json is None:
                # User provided a UID not matching any property (within the entity), make sure it's not assigned
                # elsewhere
                self._validate_uid_unassigned(prop.uid)
        else:
            if entity_json is not None:
                prop_json = self._find_property_json_by_name(entity_json, prop.name)

        if prop_json is not None:  # Load
            # Property was matched with a JSON property (either by UID or by name), make sure they're equal
            self._validate_matching_prop(entity, prop, prop_json)
            prop.iduid = IdUid.from_str(prop_json["id"])
        else:  # Assign
            if not prop.has_uid():
                prop.iduid.uid = self._generate_uid()
            prop.iduid = IdUid(entity.last_property_iduid.id + 1, prop.iduid.uid)
            entity.last_property_iduid = prop.iduid

        if prop.index is not None:
            self._load_or_assign_index(entity, prop, prop_json)

    def _load_or_assign_entity(self, entity: _Entity):
        # entity_json = None
        if entity.has_uid():
            entity_json = self._find_entity_json_by_uid(entity.uid)
            if entity_json is None:
                # User provided a UID not matching any entity, make sure it's not assigned elsewhere
                self._validate_uid_unassigned(entity.uid)
        else:
            entity_json = self._find_entity_json_by_name(entity.name)

        if entity_json is not None:  # Load
            entity.iduid = IdUid.from_str(entity_json["id"])
            entity.last_property_iduid = IdUid.from_str(entity_json["lastPropertyId"])
        else:  # Assign
            if not entity.has_uid():
                entity.iduid.uid = self._generate_uid()
            entity.iduid = IdUid(self.model.last_entity_iduid.id + 1, entity.iduid.uid)
            self.model.last_entity_iduid = entity.iduid
            entity.last_property_iduid = IdUid(0, 0)

        # Load properties
        for prop in entity.properties:
            self._load_or_assign_property(entity, prop, entity_json)

    def sync(self):
        """ Syncs the provided model with the model JSON file. """

        if self.model_json is not None:
            self.model.last_entity_iduid = IdUid.from_str(self.model_json["lastEntityId"])
            self.model.last_index_iduid = IdUid.from_str(self.model_json["lastIndexId"])
            # self.model.last_relation_iduid =

        for entity in self.model.entities:
            self._load_or_assign_entity(entity)

        self._save_model_json()


def sync_model(model: Model, model_filepath: str = "obx-model.json"):
    """ Syncs the provided model with the model JSON file. """

    id_sync = IdSync(model, model_filepath)
    id_sync.sync()
