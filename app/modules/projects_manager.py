import json
from pathlib import Path
from typing import Dict, List, Tuple

from fastapi import APIRouter, HTTPException, Query, status

from models.projects import (
    ProjectStatus, ProjectNode, ProjectEdge, ProjectGraph,
    SaveGraphRequest, SaveNodeRequest, NodeContent, FolderMetaRequest, SubprojectInfo,
    CreateNodeRequest
)
from modules.notebook_manager import VAULT_PATH, get_safe_path, sync_vault_to_git

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    responses={404: {"description": "Not found"}}
)

GRAPH_FILE_NAME = ".graph.json"
FOLDER_NOTE_FILE_NAME = "README.md"
GRID_COLS = 4
GRID_SPACING_X = 240
GRID_SPACING_Y = 160


def get_folder_path(folder: str) -> Path:
    if not folder.startswith("0_"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project folder")
    folder_path = get_safe_path(folder)
    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    return folder_path


def parse_kv_lines(lines: List[str]) -> Dict[str, str]:
    """단순 key: value 라인 파싱 (PyYAML 불필요)."""
    meta: Dict[str, str] = {}
    for line in lines:
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """md 파일 최상단 --- ~ --- 블록을 frontmatter로 파싱"""
    if not text.startswith('---'):
        return {}, text

    lines = text.split('\n')
    if lines[0].strip() != '---':
        return {}, text

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break
    if end_idx is None:
        return {}, text

    meta = parse_kv_lines(lines[1:end_idx])

    body = '\n'.join(lines[end_idx + 1:])
    if body.startswith('\n'):
        body = body[1:]
    return meta, body


def read_node_meta(file_path: Path) -> Dict[str, str]:
    try:
        text = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        text = file_path.read_text(encoding='cp949')
    meta, _ = parse_frontmatter(text)
    return meta


def ensure_folder_note(dir_path: Path) -> Path:
    """폴더의 공식 폴더노트(README.md)가 없으면 새로 만든다."""
    note_path = dir_path / FOLDER_NOTE_FILE_NAME
    if not note_path.exists():
        note_path.write_text(f'# {dir_path.name}\n', encoding='utf-8')
    return note_path


def read_folder_meta(dir_path: Path) -> Dict[str, str]:
    return read_node_meta(ensure_folder_note(dir_path))


def write_folder_meta(dir_path: Path, meta: Dict[str, str]):
    write_node_frontmatter(ensure_folder_note(dir_path), meta)


def parse_links(meta: Dict[str, str]) -> List[str]:
    """meta의 links 값('a; b; c')을 경로 리스트로 파싱"""
    return [p.strip() for p in meta.get("links", "").split(';') if p.strip()]


def format_links(links: List[str]) -> str:
    return '; '.join(links)


def write_node_frontmatter(file_path: Path, updates: Dict[str, str]):
    """md 파일 frontmatter 일부 키만 갱신 (본문은 그대로 유지)"""
    try:
        text = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        text = file_path.read_text(encoding='cp949')
    meta, body = parse_frontmatter(text)
    meta.update(updates)
    clean = {k: v for k, v in meta.items() if v}
    if clean:
        lines = ['---'] + [f'{k}: {v}' for k, v in clean.items()] + ['---', '']
        new_text = '\n'.join(lines) + body
    else:
        new_text = body
    file_path.write_text(new_text, encoding='utf-8')


def add_link(source_path: Path, target_rel_path: str):
    """source_path 노드의 metadata에 target_rel_path로의 수동 연결(links) 추가"""
    if source_path.is_dir():
        meta = read_folder_meta(source_path)
        links = parse_links(meta)
        if target_rel_path not in links:
            links.append(target_rel_path)
        meta["links"] = format_links(links)
        write_folder_meta(source_path, meta)
    else:
        links = parse_links(read_node_meta(source_path))
        if target_rel_path not in links:
            links.append(target_rel_path)
        write_node_frontmatter(source_path, {"links": format_links(links)})


def status_or_default(meta: Dict[str, str]) -> str:
    value = meta.get("status", ProjectStatus.planned.value)
    if value not in ProjectStatus._value2member_map_:
        value = ProjectStatus.planned.value
    return value


def build_tree(dir_path: Path, parent_id: str, nodes: List[dict], edges: List[dict]):
    """폴더/파일을 재귀적으로 순회해 트리 노드+엣지 목록을 채운다.
    폴더는 그 자체로 하나의 노드가 되고, 하위 파일/폴더는 거기서 뻗어나오는 sub 노드가 된다."""
    try:
        entries = sorted(dir_path.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        return

    for item in entries:
        name = item.name
        if name.startswith('.') or name == 'node_modules':
            continue
        if name == FOLDER_NOTE_FILE_NAME:
            continue  # README.md는 부모 폴더 노드의 metadata로 취급, 별도 노드로 만들지 않는다

        rel_path = str(item.relative_to(VAULT_PATH)).replace('\\', '/')

        if item.is_dir():
            meta = read_folder_meta(item)
            if meta.get("hide") == "true":
                continue  # 숨긴 프로젝트는 하위 트리 전체를 그래프에서 제외
            nodes.append({
                "path": rel_path, "name": name, "type": "folder",
                "meta": meta,
            })
            if parent_id:
                edges.append({"source": parent_id, "target": rel_path, "type": "tree"})
            build_tree(item, rel_path, nodes, edges)
        elif item.is_file() and item.suffix.lower() in ('.md', '.markdown'):
            meta = read_node_meta(item)
            nodes.append({
                "path": rel_path, "name": item.stem, "type": "file",
                "meta": meta,
            })
            if parent_id:
                edges.append({"source": parent_id, "target": rel_path, "type": "tree"})


def load_graph_layout(folder_path: Path) -> dict:
    """노드 위치(positions)만 저장. 연결 정보는 각 노드의 metadata에 저장한다."""
    graph_file = folder_path / GRAPH_FILE_NAME
    if not graph_file.exists():
        return {"positions": {}}
    try:
        return json.loads(graph_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"positions": {}}


# ===== Endpoints =====

@router.get("/top-folders", response_model=List[str])
def get_top_folders():
    """0_ 로 시작하는 최상위 프로젝트 폴더 목록"""
    if not VAULT_PATH.exists():
        return []
    return sorted(
        p.name for p in VAULT_PATH.iterdir()
        if p.is_dir() and p.name.startswith("0_")
    )


@router.get("/subprojects", response_model=List[SubprojectInfo])
def get_subprojects(folder: str = Query(..., description="0_ 로 시작하는 최상위 폴더명")):
    """해당 0_ 폴더 바로 아래의 '프로젝트' 폴더 목록 (숨김 여부 포함, 숨긴 것도 함께 반환).
    표시/숨김 관리 UI 전용 — /graph 는 숨긴 프로젝트를 아예 제외하고 반환하므로 별도 조회가 필요하다."""
    folder_path = get_folder_path(folder)
    result = []
    try:
        entries = sorted(folder_path.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        entries = []
    for p in entries:
        if not p.is_dir() or p.name.startswith('.') or p.name == 'node_modules':
            continue
        meta = read_folder_meta(p)
        result.append(SubprojectInfo(
            path=str(p.relative_to(VAULT_PATH)).replace('\\', '/'),
            name=p.name,
            hide=meta.get("hide") == "true",
            status=status_or_default(meta),
            start_date=meta.get("start_date") or None,
            end_date=meta.get("end_date") or None,
        ))
    return result


@router.get("/graph", response_model=ProjectGraph)
def get_graph(folder: str = Query(..., description="0_ 로 시작하는 최상위 폴더명")):
    """폴더 하위 트리(폴더+md 파일) 전체 + 저장된 위치/수동연결 정보를 병합해 반환.
    폴더 자체가 하나의 노드가 되고, 그 안의 파일/하위폴더는 거기서 뻗어나오는 sub 노드가 된다."""
    folder_path = get_folder_path(folder)
    layout = load_graph_layout(folder_path)
    saved_positions = layout.get("positions", {})

    raw_nodes: List[dict] = []
    tree_edges: List[dict] = []
    build_tree(folder_path, "", raw_nodes, tree_edges)

    known_paths = {n["path"] for n in raw_nodes}

    nodes: List[ProjectNode] = []
    for idx, n in enumerate(raw_nodes):
        meta = n["meta"]
        pos = saved_positions.get(n["path"])
        if pos:
            x, y = pos.get("x", 0), pos.get("y", 0)
        else:
            x = (idx % GRID_COLS) * GRID_SPACING_X
            y = (idx // GRID_COLS) * GRID_SPACING_Y

        nodes.append(ProjectNode(
            path=n["path"],
            name=n["name"],
            type=n["type"],
            folder=folder,
            status=status_or_default(meta),
            start_date=meta.get("start_date") or None,
            end_date=meta.get("end_date") or None,
            x=x,
            y=y,
        ))

    manual_edges = [
        ProjectEdge(source=n["path"], target=target, type="manual")
        for n in raw_nodes
        for target in parse_links(n["meta"])
        if target in known_paths
    ]
    edges = [ProjectEdge(**e) for e in tree_edges] + manual_edges

    return ProjectGraph(nodes=nodes, edges=edges)


@router.post("/graph")
def save_graph(request: SaveGraphRequest):
    """노드 위치는 .graph.json에, 수동 연결은 각 소스 노드의 metadata(links)에 저장 및 Git 자동 동기화.
    (부모-자식 트리 연결은 폴더 구조에서 매번 자동 계산되므로 저장하지 않는다)"""
    folder_path = get_folder_path(request.folder)

    layout = {"positions": {path: pos.model_dump() for path, pos in request.positions.items()}}

    links_by_source: Dict[str, List[str]] = {}
    for e in request.edges:
        if e.type == "manual":
            links_by_source.setdefault(e.source, []).append(e.target)

    raw_nodes: List[dict] = []
    tree_edges: List[dict] = []
    build_tree(folder_path, "", raw_nodes, tree_edges)

    try:
        graph_file = folder_path / GRAPH_FILE_NAME
        graph_file.write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding='utf-8')

        for n in raw_nodes:
            new_links = links_by_source.get(n["path"], [])
            if new_links == parse_links(n["meta"]):
                continue
            item_path = VAULT_PATH / n["path"]
            if item_path.is_dir():
                meta = read_folder_meta(item_path)
                meta["links"] = format_links(new_links)
                write_folder_meta(item_path, meta)
            else:
                write_node_frontmatter(item_path, {"links": format_links(new_links)})

        sync_vault_to_git(f"Update project graph ({request.folder})")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {"status": "success", "folder": request.folder}


@router.get("/node-content", response_model=NodeContent)
def get_node_content(path: str = Query(..., description="파일 경로")):
    """노드(md 파일) 원문 전체 조회 (frontmatter 포함, 에디터에서 그대로 편집)"""
    target_path = get_safe_path(path)
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    try:
        text = target_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        text = target_path.read_text(encoding='cp949')

    return NodeContent(path=path, content=text)


@router.post("/node")
def save_node(request: SaveNodeRequest):
    """노드(md 파일) 원문 전체 저장 (frontmatter 포함) 및 Git 자동 동기화"""
    target_path = get_safe_path(request.path)
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    try:
        target_path.write_text(request.content, encoding='utf-8')
        sync_vault_to_git(f"Update project {request.path}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {"status": "success", "path": request.path}


@router.post("/folder-meta")
def save_folder_meta(request: FolderMetaRequest):
    """폴더(프로젝트) 노드의 상태/기간을 그 폴더의 README.md frontmatter에 저장"""
    target_path = get_safe_path(request.path)
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    meta = read_folder_meta(target_path)
    if request.status is not None:
        meta["status"] = request.status.value
    if request.start_date is not None:
        meta["start_date"] = request.start_date
    if request.end_date is not None:
        meta["end_date"] = request.end_date
    if request.hide is not None:
        meta["hide"] = "true" if request.hide else "false"

    try:
        write_folder_meta(target_path, meta)
        sync_vault_to_git(f"Update project folder {request.path}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {"status": "success", "path": request.path}


@router.post("/create-node")
def create_node(request: CreateNodeRequest):
    """부모 폴더 노드 아래에 새 파일/폴더 노드 생성 (트리 연결은 폴더 구조로 자동 계산됨)"""
    parent_path = get_safe_path(request.parent_path)
    if not parent_path.exists() or not parent_path.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent folder not found")

    name = request.name.strip()
    if not name or '/' in name or '\\' in name or name in ('.', '..'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name")

    try:
        if request.type == "folder":
            target_path = parent_path / name
            if target_path.exists():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already exists")
            target_path.mkdir(parents=True)
            ensure_folder_note(target_path)
        else:
            filename = name if name.lower().endswith(('.md', '.markdown')) else f'{name}.md'
            target_path = parent_path / filename
            if target_path.exists():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already exists")
            target_path.write_text(f'---\nstatus: planned\n---\n\n# {name}\n', encoding='utf-8')

        rel_path = str(target_path.relative_to(VAULT_PATH)).replace('\\', '/')

        if request.link_from:
            link_from_path = get_safe_path(request.link_from)
            if link_from_path.exists():
                add_link(link_from_path, rel_path)

        sync_vault_to_git(f"Create project {request.type} {rel_path}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {"status": "success", "path": rel_path, "type": request.type}
