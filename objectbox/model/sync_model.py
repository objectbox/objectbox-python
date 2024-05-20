from typing import *
from objectbox.logger import logger
from objectbox.model import Model, IdUid

MODEL_PARSER_VERSION = 5


def _save_model_json(model: Model, model_filepath: str):
    # model.validate_ids_assigned()

    model_json = {
        "_note1": "KEEP THIS FILE! Check it into a version control system (VCS) like git.",
        "_note2": "ObjectBox manages crucial IDs for your object model. See docs for details.",
        "_note3": "If you have VCS merge conflicts, you must resolve them according to ObjectBox docs.",
        "entities": [],
        "lastEntityId": str(model.last_entity_id),
        "lastIndexId": str(model.last_index_id),
        "modelVersionParserMinimum": MODEL_PARSER_VERSION,
    }
    # TODO modelVersion
    # TODO retiredEntityUids
    # TODO retiredIndexUids
    # TODO retiredPropertyUids
    # TODO retiredRelationUids
    # TODO version

    for entity in model.entities:
        entity_json = {
            "id": str(entity.id),
            "name": entity.name,
            "lastPropertyId": str(entity.last_property_id),
            "properties": []
        }
        for prop in entity.properties:
            prop_json = {
                "id": str(prop.id),
                "name": prop.name,
            }
            if prop.index is not None:
                prop_json["indexId"] = str(prop.index.id)
            entity_json["properties"].append(prop_json)
        model_json["entities"].append(entity_json)

    import json
    with open(model_filepath, "w") as model_file:
        model_file.write(json.dumps(model_json, indent=2))  # Pretty


def _fetch_entity_json(model_json: Dict[str, Any], name: str):
    for entity_json in model_json["entities"]:
        if entity_json["name"] == name:
            return entity_json
    return None


def _fetch_entity_property_json(entity_json: Optional[Dict[str, Any]], name: str):
    for property_json in entity_json["properties"]:
        if property_json["name"] == name:
            return property_json
    return None


def sync_model(model: Model, model_filepath: str = "obx-model.json"):
    import json
    import random
    from os import path

    model_json = None  # ID model
    if path.exists(model_filepath):
        with open(model_filepath, "rt") as model_file:
            model_json = json.load(model_file)
        logger.debug(f"Syncing model with model file: {model_filepath}")
    else:
        logger.debug(f"Model file not found: {model_filepath}")

    if model_json is not None:
        if MODEL_PARSER_VERSION < model_json["modelVersionParserMinimum"]:
            raise Exception(f"Incompatible model file version (unparsable) "
                            f"({MODEL_PARSER_VERSION} < {model_json['modelVersionParserMinimum']})")
        model.last_entity_id = IdUid.from_str(model_json["lastEntityId"])
        model.last_index_id = IdUid.from_str(model_json["lastIndexId"])
        # TODO model.last_relation_id
    else:
        model.last_entity_id = IdUid(0, 0)
        model.last_index_id = IdUid(0, 0)
        # TODO model.last_relation_id

    def _generate_uid() -> int:
        return random.getrandbits(63) + 1  # 0 would be invalid

    for entity in model.entities:
        # Load/assign entity
        entity_json = None
        if model_json is not None:
            entity_json = _fetch_entity_json(model_json, entity.name)
        if entity_json is not None:  # Load
            entity.id = IdUid.from_str(entity_json["id"])
            assert entity.name == entity_json["name"]
            entity.last_property_id = IdUid.from_str(entity_json["lastPropertyId"])
        else:  # Assign
            entity.id = IdUid(model.last_entity_id.id + 1, _generate_uid())
            model.last_entity_id = entity.id

        # Load/assign entity's properties
        for prop in entity.properties:
            prop_json = None
            if entity_json is not None:
                prop_json = _fetch_entity_property_json(entity_json, prop.name)
            if prop_json is not None:  # Load
                prop.id = IdUid.from_str(prop_json["id"])
                assert prop.name == prop_json["name"]
                # NOTE: prop_json has indexId but prop doesn't have the index -> ignore indexId (remove it)
                if ("indexId" in prop_json) and prop.index is not None:
                    prop.index.id = IdUid.from_str(prop_json["indexId"])
            else:  # Assign
                prop.id = IdUid(entity.last_property_id.id + 1, _generate_uid())
                entity.last_property_id = prop.id
                if prop.index is not None:
                    prop.index.id = IdUid(model.last_index_id.id + 1, _generate_uid())
                    model.last_index_id = prop.index.id

    _save_model_json(model, model_filepath)  # Re-write model file
