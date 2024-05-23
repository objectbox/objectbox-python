import random
from typing import *
from objectbox.logger import logger
from objectbox.model import Model
from objectbox.model.entity import _Entity
from objectbox.model.properties import Property, Index, HnswIndex
from objectbox.model.iduid import IdUid

MODEL_PARSER_VERSION = 5


class IdSync:
    """
    Synchronizes a model with the IDs from model JSON file.
    After syncing, the model will have all IDs assigned.
    The JSON file is written (from scratch) based on the model.
    """

    def __init__(self, model: Model, model_json_filepath: str):
        self.model = model
        if len(model.entities) == 0:
            raise ValueError("A valid model must have at least one entity")

        self.model_filepath = model_json_filepath
        self.model_json = None

        self._assigned_uids: Set[int] = set()

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

        self._load_assigned_uids()

    def _load_assigned_uids(self):
        for entity_json in self.model_json["entities"]:
            entity_uid = IdUid.from_str(entity_json["id"]).uid
            if entity_uid in self._assigned_uids:
                raise ValueError(f"An entity's UID {entity_uid} has already been used elsewhere")
            self._assigned_uids.add(entity_uid)

            for prop_json in entity_json["properties"]:
                prop_uid = IdUid.from_str(prop_json["id"]).uid
                if prop_uid in self._assigned_uids:
                    raise ValueError(f"A property's UID {prop_uid} has already been used elsewhere")
                self._assigned_uids.add(prop_uid)

                if "indexId" in prop_json:
                    index_uid = IdUid.from_str(prop_json["indexId"]).uid
                    if index_uid in self._assigned_uids:
                        raise ValueError(f"An index's UID {index_uid} has already been used elsewhere")
                    self._assigned_uids.add(index_uid)

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
                "id": str(entity._iduid),
                "name": entity._name,
                "lastPropertyId": str(entity._last_property_iduid),
                "properties": []
            }
            for prop in entity._properties:
                prop_json = {
                    "id": str(prop.iduid),
                    "name": prop.name,
                    "type": prop._ob_type,
                }
                if prop._flags != 0:
                    prop_json["flags"] = prop._flags
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
        # TODO put entities in a dict (e.g. while/after loading) for faster lookup
        for entity_json in self.model_json["entities"]:
            if IdUid.from_str(entity_json["id"]).uid == uid:
                return entity_json
        return None

    def _find_entity_json_by_name(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """ Finds entity JSON by name. """
        if self.model_json is None:
            return None
        # TODO put entities in a dict (e.g. while/after loading) for faster lookup
        for entity_json in self.model_json["entities"]:
            if entity_json["name"] == entity_name:
                return entity_json
        return None

    def _find_property_json_by_uid(self, entity_json: Dict[str, Any], uid: int) -> Optional[Dict[str, Any]]:
        """ Finds entity property JSON by property UID. """
        # TODO put properties in a multi-dict (e.g. while/after loading) for faster lookup
        for prop_json in entity_json["properties"]:
            if IdUid.from_str(prop_json["id"]).uid == uid:
                return prop_json
        return None

    def _find_property_json_by_name(self, entity_json: Dict[str, Any], prop_name: str) -> Optional[Dict[str, Any]]:
        """ Finds entity property JSON by property name. """
        # TODO put properties in a multi-dict (e.g. while/after loading) for faster lookup
        for prop_json in entity_json["properties"]:
            if prop_json["name"] == prop_name:
                return prop_json
        return None

    def _generate_uid(self) -> int:
        while True:
            generated_uid = random.getrandbits(63) + 1  # 0 would be invalid
            if generated_uid not in self._assigned_uids:
                break
        self._assigned_uids.add(generated_uid)
        return generated_uid

    def _validate_uid_unassigned(self, uid: int):
        """ Validates that a user supplied UID is not assigned for any other entity/property/index.
        Raises a ValueError if the UID is already assigned elsewhere.
        """
        if uid in self._assigned_uids:
            raise ValueError(f"User supplied UID {uid} is already assigned elsewhere")

    def _validate_matching_prop(self, entity: _Entity, prop: Property, prop_json: Dict[str, Any]):
        """ Validates that the given property matches the JSON property. """
        try:
            # Don't check name equality as the property could be matched by UID (rename)
            # if validate_name and prop.name != prop_json["name"]:
            #    raise ValueError(f"name {prop.name} != name {prop_json['name']} (in JSON)")
            if prop._ob_type != prop_json["type"]:
                raise ValueError(f"OBX type {prop._ob_type} != OBX type {prop_json['type']} (in JSON)")

            json_flags = prop_json.get("flags", 0)
            if prop._flags != json_flags:
                raise ValueError(f"flags {prop._flags} != flags {json_flags} (in JSON)")

            if prop.index is None and "indexId" in prop_json:
                raise ValueError("property hasn't index, but index found in JSON")
            elif prop.index is not None and "indexId" not in prop_json:
                raise ValueError("property has index, but index not found in JSON")
        except ValueError as error:
            raise ValueError(f"Property {entity._name}.{prop.name} mismatches property found in JSON file: {error}")

    def _sync_index(self, entity: _Entity, prop: Property, prop_json: Optional[Dict[str, Any]]) -> bool:
        assert prop.index is not None
        index = prop.index

        write_json = False

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
        else:  # Assign new ID to new index
            index.iduid = IdUid(self.model.last_index_iduid.id + 1, index.uid)
            self.model.last_index_iduid = index.iduid
            write_json = True

        return write_json

    def _sync_property(self, entity: _Entity, prop: Property, entity_json: Optional[Dict[str, Any]]) -> bool:
        write_json = False

        prop_json = None
        if prop.has_uid():
            if entity_json is not None:
                prop_json = self._find_property_json_by_uid(entity_json, prop.uid)
            if prop_json is None:
                # User provided a UID not matching any property (within the entity), make sure it's not assigned
                # elsewhere
                self._validate_uid_unassigned(prop.uid)
            else:
                write_json = prop.name != prop_json["name"]  # If renaming we shall update the JSON
        else:
            if entity_json is not None:
                prop_json = self._find_property_json_by_name(entity_json, prop.name)

        if prop_json is not None:  # Load existing IDs from JSON
            # Property was matched with a JSON property (either by UID or by name), make sure they're equal
            self._validate_matching_prop(entity, prop, prop_json)
            prop.iduid = IdUid.from_str(prop_json["id"])
        else:  # Assign new ID to new property
            if not prop.has_uid():
                prop.iduid.uid = self._generate_uid()
            prop.iduid = IdUid(entity._last_property_iduid.id + 1, prop.iduid.uid)
            entity._last_property_iduid = prop.iduid
            write_json = True

        if prop.index is not None:
            write_json |= self._sync_index(entity, prop, prop_json)

        return write_json

    def _sync_entity(self, entity: _Entity) -> bool:
        write_json = False

        # entity_json = None
        if entity._has_uid():
            entity_json = self._find_entity_json_by_uid(entity._uid)
            if entity_json is None:
                # User provided a UID not matching any entity, make sure it's not assigned elsewhere
                self._validate_uid_unassigned(entity._uid)
            else:
                write_json = entity._name != entity_json["name"]  # If renaming we shall update the JSON
        else:
            entity_json = self._find_entity_json_by_name(entity._name)

        # Write JSON if the number of properties differs (to handle removed property)
        if entity_json is not None:
            write_json |= len(entity._properties) != len(entity_json["properties"])

        if entity_json is not None:  # Load existing IDs from JSON
            entity._iduid = IdUid.from_str(entity_json["id"])
            entity._last_property_iduid = IdUid.from_str(entity_json["lastPropertyId"])
        else:  # Assign new ID to new entity
            if not entity._has_uid():
                entity._iduid.uid = self._generate_uid()
            entity._iduid = IdUid(self.model.last_entity_iduid.id + 1, entity._iduid.uid)
            self.model.last_entity_iduid = entity._iduid
            entity._last_property_iduid = IdUid(0, 0)
            write_json = True

        # Load properties
        for prop in entity._properties:
            write_json |= self._sync_property(entity, prop, entity_json)

        return write_json

    def sync(self) -> bool:
        """ Syncs the provided model with the model JSON file.
        Returns True if the model JSON was written. """

        if self.model_json is not None:
            self.model.last_entity_iduid = IdUid.from_str(self.model_json["lastEntityId"])
            self.model.last_index_iduid = IdUid.from_str(self.model_json["lastIndexId"])
            # self.model.last_relation_iduid =

        write_json = False

        # Write JSON if the number of entities differs (to handle removed entity)
        if self.model_json is not None:
            write_json |= len(self.model_json["entities"]) != len(self.model.entities)

        for entity in self.model.entities:
            write_json |= self._sync_entity(entity)

        if write_json:
            logger.info(f"Model changed, writing model.json: {self.model_filepath}")
            self._save_model_json()

        self.model.on_sync()  # Notify model synced

        return write_json


def sync_model(model: Model, model_filepath: str = "objectbox-model.json") -> bool:
    """ Syncs the provided model with the model JSON file.
    Returns True if changes were made and the model JSON was written. """

    id_sync = IdSync(model, model_filepath)
    return id_sync.sync()
