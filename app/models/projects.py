from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from enum import Enum


class ProjectStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    paused = "paused"
    done = "done"


class ProjectNode(BaseModel):
    path: str = Field(..., description="vault 기준 상대 경로 (노드 id)")
    name: str = Field(..., description="파일명 또는 폴더명")
    type: Literal["file", "folder"] = "file"
    folder: str = Field(..., description="상위 0_ 최상위 폴더명")
    status: ProjectStatus = ProjectStatus.planned
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    x: float = 0
    y: float = 0


class ProjectEdge(BaseModel):
    source: str
    target: str
    type: Literal["tree", "manual"] = "manual"


class FolderMetaRequest(BaseModel):
    path: str
    status: Optional[ProjectStatus] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    hide: Optional[bool] = None


class SubprojectInfo(BaseModel):
    """0_ 최상위 폴더 바로 아래에 있는 '프로젝트' 폴더 (숨김 관리 대상)"""
    path: str
    name: str
    hide: bool = False
    status: ProjectStatus = ProjectStatus.planned
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ProjectGraph(BaseModel):
    nodes: List[ProjectNode] = Field(default_factory=list)
    edges: List[ProjectEdge] = Field(default_factory=list)


class NodePosition(BaseModel):
    x: float
    y: float


class SaveGraphRequest(BaseModel):
    folder: str
    positions: Dict[str, NodePosition]
    edges: List[ProjectEdge] = Field(default_factory=list)


class SaveNodeRequest(BaseModel):
    path: str
    content: str = Field(..., description="frontmatter 포함 파일 전체 원문")


class NodeContent(BaseModel):
    path: str
    content: str = Field(..., description="frontmatter 포함 파일 전체 원문")


class CreateNodeRequest(BaseModel):
    parent_path: str = Field(..., description="생성 위치가 될 부모 폴더 노드의 vault 기준 경로")
    name: str
    type: Literal["file", "folder"]
    link_from: Optional[str] = Field(None, description="파일 노드에서 생성한 경우, 그 파일 노드와 수동 연결(links)을 추가")
