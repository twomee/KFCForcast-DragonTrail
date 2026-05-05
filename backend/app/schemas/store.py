from pydantic import BaseModel, ConfigDict


class StoreRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

