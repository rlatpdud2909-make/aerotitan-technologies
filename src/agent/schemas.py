from pydantic import BaseModel, ConfigDict
from typing import Literal

class ExtractedField(BaseModel):
    model_config=ConfigDict(extra='forbid')
    document: Literal['PO','MTR']
    field: str
    value: str
    unit: str
    page: int
    quote: str

class Extraction(BaseModel):
    model_config=ConfigDict(extra='forbid')
    fields: list[ExtractedField]

class ToolArguments(BaseModel):
    model_config=ConfigDict(extra='forbid')
