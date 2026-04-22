from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BaselineReinitializeRequest(BaseModel):
    source_csv_path: str | None = None
    dataset_path: str | None = None
    sample_size: int | None = Field(default=None, ge=1)
    name: str = Field(default="Credit scoring baseline")
    description: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_source(self) -> "BaselineReinitializeRequest":
        if self.source_csv_path is None and self.dataset_path is None:
            raise ValueError("Either source_csv_path or dataset_path must be provided.")
        if self.dataset_path is not None and self.sample_size is None:
            raise ValueError("sample_size must be provided when dataset_path is used.")
        return self


class BaselineResponse(BaseModel):
    version: str
    name: str
    artifact_path: str
    row_count: int
    created_at: datetime
    is_active: bool
