from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ===== Folder (폴더) =====
class FolderInfo(BaseModel):
    name: str = Field(..., description="폴더명")
    path: str = Field(..., description="폴더 경로")
    parent_path: Optional[str] = Field(None, description="상위 폴더 경로")
    file_count: int = Field(0, description="하위 파일 개수")
    folder_count: int = Field(0, description="하위 폴더 개수")

# ===== Note (마크다운 파일) =====
class NoteInfo(BaseModel):
    name: str = Field(..., description="파일명 (확장자 제외)")
    file_name: str = Field(..., description="파일명 (확장자 포함)")
    path: str = Field(..., description="파일 경로")
    folder_path: str = Field(..., description="폴더 경로")
    size: int = Field(..., description="파일 크기 (bytes)")
    modified_at: datetime = Field(..., description="수정 시간")
    created_at: datetime = Field(..., description="생성 시간")

class NoteContent(BaseModel):
    info: NoteInfo
    content: str = Field(..., description="마크다운 내용")

# ===== Directory Tree (디렉토리 구조) =====
class TreeNode(BaseModel):
    name: str
    path: str
    type: str = Field(..., description="'folder' or 'file'")
    children: Optional[List['TreeNode']] = None
    size: Optional[int] = None
    modified_at: Optional[datetime] = None

# Pydantic v2에서 순환 참조 해결
TreeNode.model_rebuild()

# ===== Search Result =====
class SearchResult(BaseModel):
    files: List[NoteInfo] = Field(default_factory=list, description="검색된 파일 목록")
    total: int = Field(0, description="총 검색 결과 수")
