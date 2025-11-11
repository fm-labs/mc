from typing import Optional, Any

from pydantic import BaseModel, Field

# Standard error model (Problem Details, RFC 7807)
class Problem(BaseModel):
    #type: str = Field(default="about:blank", description="URI identifying the problem type")
    error: str = Field(..., description="Short, human-readable summary of the problem type")
    status: int = Field(..., description="HTTP status code")
    detail: Optional[str] = Field(None, description="Human-readable explanation specific to this occurrence")
    #instance: Optional[str] = Field(None, description="URI reference that identifies the specific occurrence")
    #errors: Optional[dict[str, Any]] = Field(
    #    None, description="Optional field for validation or field-specific errors"
    #)

