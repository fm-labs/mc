from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class KoProjectModel(BaseModel):
    id: str


class KoCeleryTaskSubmissionModel(BaseModel):
    task_name: str
    kwargs: dict | None = None


class KoCeleryTaskSubmissionResponseModel(BaseModel):
    task_id: str
    status: str


class KoCeleryTaskInstanceModel(BaseModel):
    task_id: str
    status: str
    task_name: Optional[str] = None
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    progress: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class KoAnsibleHostModel(BaseModel):
    hostname: str
    ip_address: Optional[str] = None
    user: Optional[str] = None
    ssh_key: Optional[str] = None
    become_user: Optional[str] = None
    become_user_ssh_key: Optional[str] = None


class KoAnsibleRunModel(BaseModel):
    run_id: str
    project_id: Optional[str] = None
    playbook: Optional[str] = None
    status: Optional[str] = None
    rc: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    events: Optional[List] = None
    stats: Optional[Dict] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    finished_at: Optional[float] = None

    def __str__(self):
        return (f"AnsibleRun(run_id={self.run_id}, status={self.status}, rc={self.rc}, "
                f"project_id={self.project_id}, playbook={self.playbook}, "
                f"stdout={self.stdout}, stderr={self.stderr})")
