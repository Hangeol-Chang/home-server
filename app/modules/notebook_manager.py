from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional
from pathlib import Path
import os
import shutil
import subprocess
from datetime import datetime
from models.notebook import (
    FolderInfo, NoteInfo, NoteContent, TreeNode, SearchResult, SaveNoteRequest, CreateFolderRequest, MoveRequest, RenameRequest
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

def should_skip(path: Path, show_hidden: bool = False) -> bool:
    """숨김 파일/폴더 또는 .git 등 제외"""
    name = path.name
    # 항상 제외
    if name in ('.git', 'node_modules'):
        return True
    # 숨김 표시 off일 때만 점(.)으로 시작하는 항목 제외
    if not show_hidden and (name.startswith('.') or name.startswith('_')):
        return True
    return False

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
def get_directory_tree(path: str = Query("", description="조회할 경로")):
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
def get_folders(
    path: str = Query("", description="조회할 경로"),
    show_hidden: bool = Query(False, description="숨김 항목(.으로 시작) 표시 여부")
):
    """특정 경로의 하위 폴더 목록 조회"""
    target_path = get_safe_path(path)

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    folders = []
    for item in sorted(target_path.iterdir(), key=lambda x: x.name.lower()):
        if not item.is_dir() or should_skip(item, show_hidden):
            continue

        relative_path = str(item.relative_to(VAULT_PATH)).replace('\\', '/')
        parent_path = str(item.parent.relative_to(VAULT_PATH)).replace('\\', '/') if item.parent != VAULT_PATH else ""

        file_count = sum(1 for f in item.iterdir() if f.is_file() and is_markdown_file(f) and not should_skip(f, show_hidden))
        folder_count = sum(1 for f in item.iterdir() if f.is_dir() and not should_skip(f, show_hidden))

        folders.append(FolderInfo(
            name=item.name,
            path=relative_path,
            parent_path=parent_path if parent_path else None,
            file_count=file_count,
            folder_count=folder_count
        ))

    return folders

@router.get("/files", response_model=List[NoteInfo])
def get_files(
    path: str = Query("", description="조회할 폴더 경로"),
    show_hidden: bool = Query(False, description="숨김 항목(.으로 시작) 표시 여부")
):
    """특정 폴더의 마크다운 파일 목록 조회"""
    target_path = get_safe_path(path)

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    files = []
    for item in sorted(target_path.iterdir(), key=lambda x: x.name.lower()):
        if not item.is_file() or should_skip(item, show_hidden):
            continue

        files.append(get_file_info(item, VAULT_PATH))

    return files

@router.get("/content", response_model=NoteContent)
def get_file_content(path: str = Query(..., description="파일 경로")):
    """마크다운 파일 내용 조회"""
    target_path = get_safe_path(path)
    
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        content = target_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = target_path.read_text(encoding='cp949')
        except UnicodeDecodeError:
            content = f"[바이너리 파일 — 텍스트로 표시할 수 없습니다: {target_path.name}]"
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
def search_notes(
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
def get_vault_stats():
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

# ===== Git Integration =====

REPO_PATH = VAULT_PATH.parent  # home-server 루트 레포
VAULT_BRANCH = "home-server"   # obsidian-vault에서 사용할 브랜치


def run_git_command(commands: List[str], cwd: Path = None):
    """Git 명령어 실행"""
    try:
        subprocess.run(
            commands,
            cwd=cwd or VAULT_PATH,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e.stderr}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Git error: {e.stderr}"
        )


def ensure_vault_branch():
    """obsidian-vault가 VAULT_BRANCH 브랜치에 있도록 보장 (없으면 생성 후 checkout)"""
    # vault 경로 및 git 초기화 여부 확인
    if not VAULT_PATH.exists():
        raise RuntimeError(f"obsidian-vault 디렉토리가 없습니다: {VAULT_PATH}\n'git submodule update --init'을 실행하세요.")

    git_dir = VAULT_PATH / ".git"
    if not git_dir.exists():
        raise RuntimeError(f"obsidian-vault가 git 저장소가 아닙니다: {VAULT_PATH}\n'git submodule update --init'을 실행하세요.")

    # 현재 브랜치 확인 (detached HEAD면 빈 문자열)
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=VAULT_PATH, capture_output=True, text=True
    )
    current = result.stdout.strip()
    if current == VAULT_BRANCH:
        return

    # 로컬 브랜치 존재 여부 확인
    result = subprocess.run(
        ["git", "branch", "--list", VAULT_BRANCH],
        cwd=VAULT_PATH, capture_output=True, text=True
    )
    if VAULT_BRANCH in result.stdout:
        subprocess.run(
            ["git", "checkout", VAULT_BRANCH],
            cwd=VAULT_PATH, check=True, capture_output=True, text=True
        )
    else:
        # 로컬 없으면 리모트 확인
        result = subprocess.run(
            ["git", "branch", "-r", "--list", f"origin/{VAULT_BRANCH}"],
            cwd=VAULT_PATH, capture_output=True, text=True
        )
        if f"origin/{VAULT_BRANCH}" in result.stdout:
            subprocess.run(
                ["git", "checkout", "-b", VAULT_BRANCH, "--track", f"origin/{VAULT_BRANCH}"],
                cwd=VAULT_PATH, check=True, capture_output=True, text=True
            )
        else:
            subprocess.run(
                ["git", "checkout", "-b", VAULT_BRANCH],
                cwd=VAULT_PATH, check=True, capture_output=True, text=True
            )
    print(f"[notebook] Switched obsidian-vault to branch '{VAULT_BRANCH}' (was: '{current or 'detached HEAD'}')")


def update_parent_submodule_pointer(vault_commit_message: str):
    """home-server 레포의 obsidian-vault 서브모듈 포인터를 최신으로 갱신"""
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain", "obsidian-vault"],
            cwd=REPO_PATH, capture_output=True, text=True
        )
        if not status_result.stdout.strip():
            return

        subprocess.run(
            ["git", "add", "obsidian-vault"],
            cwd=REPO_PATH, check=True, capture_output=True, text=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"chore: update obsidian-vault pointer ({vault_commit_message})"],
            cwd=REPO_PATH, check=True, capture_output=True, text=True
        )
        subprocess.run(
            ["git", "push"],
            cwd=REPO_PATH, check=True, capture_output=True, text=True
        )
        print("Parent submodule pointer updated.")
    except subprocess.CalledProcessError as e:
        # 포인터 갱신 실패는 vault 작업 자체를 막지 않도록 경고만 출력
        print(f"update_parent_submodule_pointer failed: {e.stderr}")


def is_git_repo(path: Path) -> bool:
    """해당 경로가 유효한 git 저장소인지 확인"""
    git_dir = path / ".git"
    if not git_dir.exists():
        return False
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path, capture_output=True, text=True
    )
    return result.returncode == 0


def sync_vault_to_git(commit_message: str):
    """Vault 변경사항을 Git에 커밋하고 푸시한 뒤 부모 레포 서브모듈 포인터도 갱신.
    .git이 없는 환경(Mutagen sync 등)에서는 git 작업을 건너뜀."""
    if not is_git_repo(VAULT_PATH):
        print(f"[notebook] .git 없음 — git sync 건너뜀 ({commit_message})")
        return

    # 1. home-server 브랜치 보장
    ensure_vault_branch()

    # 2. 변경사항 확인
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=VAULT_PATH, capture_output=True, text=True
    )
    if not status_result.stdout.strip():
        return

    # 3. Add / Commit / Push (submodule)
    run_git_command(["git", "add", "."])
    run_git_command(["git", "commit", "-m", commit_message])
    run_git_command(["git", "push", "--set-upstream", "origin", VAULT_BRANCH])

    # 4. 부모 레포 서브모듈 포인터 갱신
    update_parent_submodule_pointer(commit_message)

@router.get("/git-status")
def git_status():
    """obsidian-vault와 부모 레포의 git 상태 반환 (디버그용)"""
    def run(cmds, cwd):
        r = subprocess.run(cmds, cwd=cwd, capture_output=True, text=True)
        return r.stdout.strip() or r.stderr.strip()

    vault_git = is_git_repo(VAULT_PATH)
    repo_git = is_git_repo(REPO_PATH)

    return {
        "vault": {
            "path": str(VAULT_PATH),
            "git_available": vault_git,
            **(
                {
                    "branch": run(["git", "branch", "--show-current"], VAULT_PATH),
                    "status": run(["git", "status", "--short"], VAULT_PATH),
                    "last_commit": run(["git", "log", "-1", "--oneline"], VAULT_PATH),
                    "remotes": run(["git", "remote", "-v"], VAULT_PATH),
                } if vault_git else {"note": ".git 없음 — Mutagen sync 환경으로 추정"}
            )
        },
        "repo": {
            "path": str(REPO_PATH),
            "git_available": repo_git,
            **(
                {
                    "branch": run(["git", "branch", "--show-current"], REPO_PATH),
                    "submodule_status": run(["git", "submodule", "status"], REPO_PATH),
                    "last_commit": run(["git", "log", "-1", "--oneline"], REPO_PATH),
                } if repo_git else {"note": ".git 없음"}
            )
        }
    }


@router.post("/git-pull")
def git_pull():
    """Git Pull 실행 (home-server 브랜치 보장 후 pull)"""
    try:
        ensure_vault_branch()

        result = subprocess.run(
            ["git", "pull", "origin", VAULT_BRANCH],
            cwd=VAULT_PATH,
            capture_output=True,
            text=True,
            check=True
        )

        return {
            "success": True,
            "message": result.stdout,
            "timestamp": datetime.now().isoformat()
        }
    except subprocess.CalledProcessError as e:
        print(f"Git pull failed: {e.stderr}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Git pull error: {e.stderr}"
        )

@router.post("/save")
def save_note(request: SaveNoteRequest):
    """노트 저장 및 Git 자동 동기화"""
    target_path = get_safe_path(request.path)

    try:
        # 상위 디렉토리 생성
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일 쓰기
        target_path.write_text(request.content, encoding='utf-8')
        
        # Git 커밋 메시지 설정
        msg = request.commit_message or f"Update {request.path} via Web"
        
        # Git 동기화
        sync_vault_to_git(msg)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return {"status": "success", "path": request.path}

@router.delete("/file")
def delete_file(path: str = Query(..., description="삭제할 파일 경로")):
    """파일 삭제 및 Git 자동 동기화"""
    target_path = get_safe_path(path)

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    try:
        target_path.unlink()
        sync_vault_to_git(f"Delete {path}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return {"status": "success", "path": path}


@router.delete("/folder")
def delete_folder(path: str = Query(..., description="삭제할 폴더 경로")):
    """폴더 삭제 및 Git 자동 동기화"""
    target_path = get_safe_path(path)

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    try:
        shutil.rmtree(target_path)
        sync_vault_to_git(f"Delete folder {path}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return {"status": "success", "path": path}


@router.post("/move")
def move_item(request: MoveRequest):
    """파일 또는 폴더를 다른 위치로 이동"""
    src = get_safe_path(request.src_path)

    if not src.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    dest_folder = get_safe_path(request.dest_folder) if request.dest_folder else VAULT_PATH
    if not dest_folder.exists() or not dest_folder.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Destination folder not found")

    # 자기 자신 또는 하위 폴더로의 이동 방지
    try:
        dest_folder.relative_to(src)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot move a folder into itself")
    except ValueError:
        pass

    dest = dest_folder / src.name
    if dest.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{src.name}' already exists in destination")

    try:
        shutil.move(str(src), str(dest))
        sync_vault_to_git(f"Move {request.src_path} → {request.dest_folder or '/'}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    dest_relative = str(dest.relative_to(VAULT_PATH)).replace('\\', '/')
    return {"status": "success", "src_path": request.src_path, "dest_path": dest_relative}


@router.post("/rename")
def rename_item(request: RenameRequest):
    """파일 또는 폴더 이름 변경"""
    src = get_safe_path(request.src_path)
    if not src.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    new_name = request.new_name.strip()
    if not new_name or '/' in new_name or '\\' in new_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name")

    dest = src.parent / new_name
    if dest.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{new_name}' already exists")

    try:
        src.rename(dest)
        sync_vault_to_git(f"Rename {src.name} → {new_name}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    dest_relative = str(dest.relative_to(VAULT_PATH)).replace('\\', '/')
    return {"status": "success", "new_path": dest_relative, "new_name": new_name}


@router.post("/folder")
def create_folder(request: CreateFolderRequest):
    """폴더 생성 및 Git 자동 동기화"""
    target_path = get_safe_path(request.path)
    
    if target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder already exists"
        )
    
    try:
        # 폴더 생성
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Git은 빈 폴더를 추적하지 않으므로 .gitkeep 파일 생성
        gitkeep_path = target_path / ".gitkeep"
        gitkeep_path.touch()
        
        # Git 커밋 메시지 설정
        msg = request.commit_message or f"Create folder {request.path}"
        
        # Git 동기화
        sync_vault_to_git(msg)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return {"status": "success", "path": request.path}
