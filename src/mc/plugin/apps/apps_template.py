from typing import Literal, Any

import pydantic


class AppTemplate(pydantic.BaseModel):
    version: str
    type: Literal["container", "compose"]
    title: str | None = None
    description: str | None = None
    image: str | None = None # only container
    stackfile: str | None = None # only compose
    vars: dict[str, dict[str, Any]] | None = None
    #volumes: dict[str, dict[str, Any]] | None = None
    #services: dict[str, dict[str, Any]] | None = None

    def from_dict(self, template: dict) -> AppTemplate:
        # todo parse spec from json
        pass

    def from_json(self, template: str) -> AppTemplate:
        # todo parse spec from json
        pass

    def from_url(self, url: str) -> AppTemplate:
        # todo download spec from url
        pass

    #def from_template_repository(self, repository: str, stackfile: str) -> AppTemplate:
    #    # todo clone repo to temp location, copy stackfile to project_dir
    #    pass