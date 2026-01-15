"""Pydantic models for Orca integration configuration."""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class LocalizedName(BaseModel):
    """Represents the bilingual name field."""

    en: str
    si: str


class NumericRange(BaseModel):
    """Represents the min/max/step for adjustable values.

    Default values used as range is not always present in input.
    """

    min: float = 0.0
    max: float = 0.0
    step: float = 0.0


class AdjustableSettings(BaseModel):
    """Represents the 'adjustable' block.

    If 'range' is missing in YAML, the default factory creates an empty NumericRange.
    """

    enabled: bool
    range: NumericRange = Field(default_factory=NumericRange)


class BaseSensor(BaseModel):
    """Parent class containing common fields for all sensor types."""

    tag: str
    id: str
    unique_id: str | None = Field(default=None)  # set afterwards
    name: LocalizedName
    description: str = ""  # Default empty string if missing
    heating_circuit: int
    adjustable: AdjustableSettings = Field(default_factory=AdjustableSettings)


class FloatSensor(BaseSensor):
    """Model for items where type is 'float'."""

    type: Literal["float"]
    unit: str


class BooleanSensor(BaseSensor):
    """Model for items where type is 'boolean'."""

    type: Literal["boolean"]


class MultimodeSensor(BaseSensor):
    """Model for items where type is 'multimode'."""

    type: Literal["multimode"]
    # Maps integer keys to string descriptions (e.g., 1: "heat")
    value_map: dict[int, str] = Field(default_factory=dict)


# Union type that uses the 'type' field to determine which model to validate against
OrcaTagConfig = Annotated[
    Union[FloatSensor, MultimodeSensor, BooleanSensor], Field(discriminator="type")
]
