"""Modelos Pydantic: validan lo que entra a la API y describen lo que sale."""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

Status = Literal["pending", "done"]

# Texto sin espacios sobrantes en los extremos. `strict` impide que un número
# o un booleano se conviertan en texto sin avisar.
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200, strict=True)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000, strict=True)]


class TodoCreate(BaseModel):
    # Rechaza campos desconocidos (por ejemplo, intentar fijar "id" o "status").
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: Optional[Description] = None


class TodoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[Title] = None
    description: Optional[Description] = None
    status: Optional[Status] = None

    @model_validator(mode="after")
    def check_fields(self) -> "TodoUpdate":
        if not self.model_fields_set:
            raise ValueError("Hay que enviar al menos un campo: title, description o status")
        # description puede ser null (borra la descripción); title y status no.
        for field in ("title", "status"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class Todo(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: Status
    created_at: str
    updated_at: str
