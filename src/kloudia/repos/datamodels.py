from pydantic import BaseModel


class KloudiaRepoModel(BaseModel):
    name: str
    url: str
    description: str | None = None
    private: bool | None = False
    default_branch: str | None = "main"
    ssh_url: str | None = None