from datetime import datetime, timezone
from typing import TypeVar

from bson import ObjectId
from pydantic import BaseModel, ConfigDict
from pydantic_core import core_schema

M = TypeVar("M", bound="BaseDocument")


class ObjIdStr(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.any_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, value: object) -> str:
        return str(value)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_oid(value: str | ObjectId | None) -> ObjectId | None:
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    return ObjectId(value)


def to_mongo(model: BaseModel, *, exclude: set[str] | None = None) -> dict:
    excluded = {"id"} | (exclude or set())
    data = model.model_dump(exclude_none=True, exclude=excluded)
    data.pop("_id", None)
    data.pop("id", None)
    return data


def doc_to_model(model_type: type[M], doc: dict | None) -> M | None:
    if doc is None:
        return None
    payload = {k: v for k, v in doc.items() if k != "_id"}
    payload["id"] = str(doc["_id"])
    return model_type.model_validate(payload)


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: str | None = None