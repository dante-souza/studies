# GERADO por 05_modelos_a_partir_de_especificacao.ipynb a partir de configs/models.yaml — NÃO EDITAR À MÃO.
# Para mudar um modelo, edite a especificação e regenere. Regra de negócio: subclasses em outro módulo.
from datetime import date, datetime
from decimal import Decimal
from enum import IntEnum, StrEnum
from typing import Annotated

from pydantic import UUID4, AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field
from pydantic.alias_generators import to_camel

from validadores import NORMALIZERS, VALIDATORS


class BodyType(StrEnum):
    SEDAN = 'sedan'
    COUPE = 'coupe'
    SUV = 'suv'
    TRUCK = 'truck'


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class RegistrationCountry(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)

    name: Annotated[str, Field(min_length=2), AfterValidator(VALIDATORS['no_digits'])]
    code3: Annotated[str, Field(pattern='^[A-Z]{3}$')]


class Automobile(BaseModel):
    'Carro do projeto do curso'
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, validate_assignment=True, alias_generator=to_camel, validate_by_name=True)

    manufacturer: Annotated[str, Field(min_length=2, max_length=50), BeforeValidator(NORMALIZERS['strip_title'])]
    body_type: BodyType
    manufactured_date: Annotated[date, Field(ge=date(1980, 1, 1))]
    number_of_doors: Annotated[int, Field(ge=2, le=4)] = Field(default=4)
    registration_country: RegistrationCountry | None = Field(default=None)
    top_features: list[str] = Field(default=[])


class ServiceTicket(BaseModel):
    'Chamado de manutenção'
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, validate_assignment=True, alias_generator=to_camel, validate_by_name=True)

    vin: Annotated[str, Field(pattern='^[A-HJ-NPR-Z0-9]{17}$'), BeforeValidator(NORMALIZERS['upper'])]
    priority: Priority = Field(default=Priority.MEDIUM)
    opened_at: datetime
    car: Automobile
