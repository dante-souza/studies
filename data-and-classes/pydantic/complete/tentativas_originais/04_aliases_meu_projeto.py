from datetime import date
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


def make_alias(field_name: str) -> str:
    alias = to_camel(field_name)
    return alias.removesuffix("_")

class AutomobileType(Enum):
    sedan = "Sedan"
    coupe = "Coupe"
    convertible = "Convertible"
    suv = "SUV"
    truck = "Truck"


class Automobile(BaseModel):
    """
    Modify your `Automobile` model to implement the following:
    - auto generate camel case aliases
    - the field `type_` in our model is provided as `type` in source data, and should also serialize to `type`.
    - the data we receive contains the following field names that need to map to our own model field names - but we still
    want our camelized field names to be used for serialization. Account for that (without renaming the field names):
        - `number_of_doors` is provided as `doors`
        - `manufactured_date` is provided as `completionDate`
    - The field `base_msrp_usd` is provided as `msrpUSD`, and we want the serialization name to be `baseMSRPUSD`
    - we want the JSON serialized output of `manufactured_date` to be this pattern: `YYYY/MM/DD` (e.g. `2020/01/01`),
    but serializing to a Python dict should remain as a `date` object.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        alias_generator=make_alias,
    )

    manufacturer: str
    series_name: str
    type_: AutomobileType
    is_electric: bool = False
    manufactured_date: date = Field(alias="completionDate", )
    base_msrp_usd: float = Field(
        validation_alias="msrpUSD", # deserialization alias - load
        serialization_alias="baseMSRPUSD" # serialization alias - dump
    )
    vin: str
    number_of_doors: int = Field(alias="doors", default=4)
    registration_country: str | None = None
    license_plate: str | None = None