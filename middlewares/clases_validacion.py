from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExportacionFijaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    etiqueta: str
    valor: str


class FrontendSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    tipo_input: Optional[str] = None


class ExportacionDcSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    etiqueta: str
    etiqueta_final_alma: Optional[str] = None


class SchemaItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campo: str
    es_multiple: bool
    requerido: bool
    frontend: FrontendSchema
    exportacion_dc: Optional[ExportacionDcSchema] = None  # Puede ser null o no venir


class NuevaColeccionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre_coleccion: str = Field(..., min_length=1)
    origen: Optional[Literal["acervo", "tesis"]] = None
    exportacion_fija: List[ExportacionFijaSchema] = Field(default_factory=list)
    schema_: List[SchemaItemSchema] = Field(default_factory=list, alias="schema")


class NuevaSubcoleccionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre_subcoleccion: str = Field(..., min_length=1)
    coleccion_internal_id: str = Field(..., min_length=1)


class ColeccionInParent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_collection: str = Field(..., min_length=1)
    setspec_collection: str = Field(..., min_length=1)
    internal_id: str = Field(..., min_length=1)


class SubcoleccionInParent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_subcollection: str = Field(..., min_length=1)
    setspec_subcollection: str = Field(..., min_length=1)
    internal_id: str = Field(..., min_length=1)


class ParentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coleccion: ColeccionInParent
    subcoleccion: SubcoleccionInParent
