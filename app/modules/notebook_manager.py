from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from pathlib import Path
import os
from datetime import datetime
from models.notebook import (
    FolderInfo, NoteInfo, NoteContent, TreeNode, SearchResult
)

# 라우터 생성
router = APIRouter(
    prefix="/notebook",
    tags=["Notebook"],
    responses={404: {"description": "Not found"}}
)

# Obsidian vault 경로 설정
VAULT_PATH = Path(__file__).parent.parent.parent / "obsidian-vault"

def get_safe_path(relative_path: str = "") -> Path:
    """안전한 경로 반환 (경로 탐색 공격 방지)"""
    if not relative_path:
        return VAULT_PATH
    
    full_path = (VAULT_PATH / relative_path).resolve()
    
    # VAULT_PATH 외부로 벗어나는지 확인
    try:
        full_path.relative_to(VAULT_PATH.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path"
        )
    
    return full_path

def is_markdown_file(file_path: Path) -> bool:
    """마크다운 파일인지 확인"""
    return file_path.suffix.lower() in ['.md', '.markdown']

def should_skip(path: Path) -> bool:
    """숨김 파일/폴더 또는 .git 등 제외"""
    name = path.name
    return name.startswith('.') or name.startswith('_') or name == 'node_modules'

def get_file_info(file_path: Path, vault_path: Path) -> NoteInfo:
    """파일 정보 추출"""
    stat = file_path.stat()
    relative_path = str(file_path.relative_to(vault_path))
    folder_path = str(file_path.parent.relative_to(vault_path)) if file_path.parent != vault_path else ""
    
    return NoteInfo(
        name=file_path.stem,
        file_name=file_path.name,
        path=relative_path.replace('\\', '/'),
        folder_path=folder_path.replace('\\', '/'),
        size=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        created_at=datetime.fromtimestamp(stat.st_ctime)
    )

# ===== API Endpoints =====

@router.get("/tree", response_model=TreeNode)
async def get_directory_tree(path: str = Query("", description="조회할 경로")):
    """디렉토리 트리 구조 조회"""
    target_path = get_safe_path(path)
    
    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Path not found"
        )
    
    def build_tree(current_path: Path) -> TreeNode:
        if current_path.is_file():
            if not is_markdown_file(current_path):
                return None
            
            stat = current_path.stat()
            relative_path = str(current_path.relative_to(VAULT_PATH)).replace('\\', '/')
            
            return TreeNode(
                name=current_path.name,
                path=relative_path,
                type="file",
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime)
            )
        
        # 디렉토리인 경우
        children = []
        try:
            for item in sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if should_skip(item):
                    continue
                
                child = build_tree(item)
                if child:
                    children.append(child)
        except PermissionError:
            pass
        
        relative_path = str(current_path.relative_to(VAULT_PATH)).replace('\\', '/') if current_path != VAULT_PATH else ""
        
        return TreeNode(
            name=current_path.name if current_path != VAULT_PATH else "obsidian-vault",
            path=relative_path,
            type="folder",
            children=children if children else None
        )
    
    tree = build_tree(target_path)
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid content found"
        )
    
    return tree

@router.get("/folders", response_model=List[FolderInfo])
async def get_folders(path: str = Query("", description="조회할 경로")):
    """특정 경로의 하위 폴더 목록 조회"""
    target_path = get_safe_path(path)
    
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    folders = []
    for item in sorted(target_path.iterdir(), key=lambda x: x.name.lower()):
        if not item.is_dir() or should_skip(item):
            continue
        
        relative_path = str(item.relative_to(VAULT_PATH)).replace('\\', '/')
        parent_path = str(item.parent.relative_to(VAULT_PATH)).replace('\\', '/') if item.parent != VAULT_PATH else ""
        
        # 하위 파일/폴더 개수 계산
        file_count = sum(1 for f in item.iterdir() if f.is_file() and is_markdown_file(f) and not should_skip(f))
        folder_count = sum(1 for f in item.iterdir() if f.is_dir() and not should_skip(f))
        
        folders.append(FolderInfo(
            name=item.name,
            path=relative_path,
            parent_path=parent_path if parent_path else None,
            file_count=file_count,
            folder_count=folder_count
        ))
    
    return folders

@router.get("/files", response_model=List[NoteInfo])
async def get_files(path: str = Query("", description="조회할 폴더 경로")):
    """특정 폴더의 마크다운 파일 목록 조회"""
    target_path = get_safe_path(path)
    
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    files = []
    for item in sorted(target_path.iterdir(), key=lambda x: x.name.lower()):
        if not item.is_file() or not is_markdown_file(item) or should_skip(item):
            continue
        
        files.append(get_file_info(item, VAULT_PATH))
    
    return files

@router.get("/content", response_model=NoteContent)
async def get_file_content(path: str = Query(..., description="파일 경로")):
    """마크다운 파일 내용 조회"""
    target_path = get_safe_path(path)
    
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not is_markdown_file(target_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a markdown file"
        )
    
    try:
        content = target_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = target_path.read_text(encoding='cp949')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read file: {str(e)}"
            )
    
    return NoteContent(
        info=get_file_info(target_path, VAULT_PATH),
        content=content
    )

@router.get("/search", response_model=SearchResult)
async def search_notes(
    query: str = Query(..., min_length=1, description="검색어"),
    path: str = Query("", description="검색할 폴더 경로"),
    in_content: bool = Query(False, description="내용도 검색할지 여부")
):
    """노트 검색 (파일명 또는 내용)"""
    target_path = get_safe_path(path)
    
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    results = []
    query_lower = query.lower()
    
    def search_recursive(current_path: Path):
        try:
            for item in current_path.iterdir():
                if should_skip(item):
                    continue
                
                if item.is_dir():
                    search_recursive(item)
                elif item.is_file() and is_markdown_file(item):
                    # 파일명 검색
                    if query_lower in item.stem.lower():
                        results.append(get_file_info(item, VAULT_PATH))
                    # 내용 검색 (옵션)
                    elif in_content:
                        try:
                            content = item.read_text(encoding='utf-8').lower()
                            if query_lower in content:
                                results.append(get_file_info(item, VAULT_PATH))
                        except:
                            pass
        except PermissionError:
            pass
    
    search_recursive(target_path)
    
    # 수정 시간 기준 정렬
    results.sort(key=lambda x: x.modified_at, reverse=True)
    
    return SearchResult(
        files=results,
        total=len(results)
    )

@router.get("/stats")
async def get_vault_stats():
    """Vault 통계 정보"""
    if not VAULT_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault not found"
        )
    
    total_files = 0
    total_folders = 0
    total_size = 0
    
    def count_recursive(current_path: Path):
        nonlocal total_files, total_folders, total_size
        
        try:
            for item in current_path.iterdir():
                if should_skip(item):
                    continue
                
                if item.is_dir():
                    total_folders += 1
                    count_recursive(item)
                elif item.is_file() and is_markdown_file(item):
                    total_files += 1
                    total_size += item.stat().st_size
        except PermissionError:
            pass
    
    count_recursive(VAULT_PATH)
    
    return {
        "total_files": total_files,
        "total_folders": total_folders,
        "total_size": total_size,
        "vault_path": str(VAULT_PATH)
    }
