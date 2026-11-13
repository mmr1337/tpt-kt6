from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class Pet(BaseModel):
    model_config = ConfigDict(strict=True)

    id: int
    name: str
    photoUrls: list[str] = Field(default_factory=list)
    status: Literal["available", "pending", "sold"] = "available"


class Order(BaseModel):
    model_config = ConfigDict(strict=True)

    id: int
    petId: int
    quantity: int = Field(default=1, gt=0)
    status: Literal["placed", "approved", "delivered"] = "placed"
    complete: bool = False


class Inventory(RootModel[dict[str, Annotated[int, Field(strict=True, ge=0)]]]):
    pass
