import os
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import requests
from models.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    MessageRole
)
from modules.workspace_tools import execute_tool_call, WORKSPACE_PATH

# 라우터 생성
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}}
)

# ===== 모델 설정 =====

# Ollama 설정
# 로컬에서 실행할 경우 "http://127.0.0.1:11434"
# 별도 서버에서 실행될 경우 예) "http://hihangeol.duckdns.org:11434"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://hihangeol.duckdns.org:11434")
OLLAMA_MODEL_CHAT = os.getenv("OLLAMA_MODEL_CHAT", "qwen2.5-coder:14b")

MAX_TOOL_ITERATIONS = 10  # 무한 루프 방지

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful home server assistant running on a Raspberry Pi. "
    "You have access to the user's workspace filesystem via tools. "
    "When the user asks about files or code, use the tools to explore and read them. "
    "When asked to modify files, use write_file after reading the original content first. "
    "Always answer in the same language the user uses."
)

# ===== Ollama Tool Schema =====
# Ollama/OpenAI 호환 JSON Schema 형식의 Tools 정의
OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "워크스페이스 내 디렉토리 목록을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "조회할 상대 경로 (예: 'home-server/app'). 기본값: 루트"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "워크스페이스 내 파일의 내용을 읽습니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "읽을 파일의 상대 경로 (예: 'home-server/app/main.py')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "워크스페이스 내 파일에 내용을 씁니다. 파일이 없으면 생성하고, 있으면 전체를 덮어씁니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "쓸 파일의 상대 경로"
                    },
                    "content": {
                        "type": "string",
                        "description": "파일에 쓸 전체 내용"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "glob 패턴으로 파일을 검색합니다. 예) pattern='**/*.py' 로 모든 파이썬 파일 검색",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "glob 패턴 (예: '**/*.py', '*.md')"
                    },
                    "directory": {
                        "type": "string",
                        "description": "검색 시작 디렉토리 상대 경로. 기본값: 루트"
                    }
                },
                "required": ["pattern"]
            }
        }
    }
]

# ===== Ollama 로직 =====

def build_ollama_messages(history: List[ChatMessage], message: str, system_prompt: str) -> List[Dict[str, Any]]:
    """Ollama API에 전달할 메시지 구조체를 구성"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    for msg in history:
        messages.append({
            "role": "user" if msg.role == MessageRole.user else "assistant",
            "content": msg.content
        })
    
    messages.append({"role": "user", "content": message})
    return messages

def call_ollama(messages: List[Dict[str, Any]]) -> str:
    """Ollama API 호출 + Tool 실행 Agentic Loop"""
    messages_copy = messages.copy() # 루프 돌 동안 메시지 누적
    
    for iteration in range(MAX_TOOL_ITERATIONS):
        payload = {
            "model": OLLAMA_MODEL_CHAT,
            "messages": messages_copy,
            "stream": False,
            "tools": OLLAMA_TOOLS
        }

        try:
            # 1. Ollama API POST 호출
            url = f"{OLLAMA_BASE_URL}/api/chat"
            print(f"[Ollama] Requesting {url} with model {OLLAMA_MODEL_CHAT}")
            
            # 공유기 내부망(NAT Loopback 미지원) 등에서 외부 DDNS 도메인으로의 라우팅이 막혀있을 수 있으므로
            # ConnectionError 발생 시 localhost(127.0.0.1) 경로로 우회하여 재시도합니다.
            try:
                response = requests.post(url, json=payload, timeout=300)
                if response.status_code != 200:
                    print(f"[Ollama] Error Body: {response.text}")
                response.raise_for_status()
            except requests.exceptions.ConnectionError:
                fallback_url = "http://127.0.0.1:11434/api/chat"
                print(f"[Ollama] Connection error with {url}, falling back to {fallback_url}")
                response = requests.post(fallback_url, json=payload, timeout=300)
                if response.status_code != 200:
                    print(f"[Ollama] Fallback Error Body: {response.text}")
                response.raise_for_status()

            data = response.json()
        except requests.exceptions.RequestException as e:
            # 타임아웃, 연결 거부 등의 오류 시 상세 원인 포함
            error_msg = f"Ollama API 호출 네트워크 (URL: {OLLAMA_BASE_URL}): {str(e)}"
            print(f"[Ollama Error] {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Ollama API 호출 시스템 오류: {str(e)}"
            print(f"[Ollama Error] {error_msg}")
            raise Exception(error_msg)

        assistant_message = data.get("message", {})
        
        # 2. Tool 호출 여부 확인
        tool_calls = assistant_message.get("tool_calls", [])
        
        if not tool_calls:
            # 툴 호출이 없으면 최종 텍스트 반환
            return assistant_message.get("content", "")

        # 3. 모델의 툴 호출을 메시지에 누적 저장
        messages_copy.append({
            "role": assistant_message.get("role", "assistant"),
            "content": assistant_message.get("content", ""),
            "tool_calls": tool_calls
        })

        # 4. 각 툴 실행 결과를 메시지 내역(role: tool)에 추가하여 다시 LLM 확인 (반복)
        for tool_call in tool_calls:
            func = tool_call.get("function", {})
            name = func.get("name")
            args = func.get("arguments", {})
            
            print(f"[workspace] Ollama tool call: {name}({args})")
            
            result = execute_tool_call(name, args)
            
            messages_copy.append({
                "role": "tool",
                "name": name,
                "content": str(result)
            })

    return "무한 루프 방지: 최대 도구 실행 횟수(10회)에 도달했습니다."


# ===== API Endpoints =====

@router.post("/message", response_model=ChatResponse)
def send_message(request: ChatRequest):
    """
    Ollama(qwen2.5-coder:14b)로 요청.
    - 프론트엔드 → 백엔드 → Ollama API 백엔드로 요청 체이닝.
    """
    system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT

    try:
        messages = build_ollama_messages(request.history, request.message, system_prompt)
        reply_text = call_ollama(messages)
        used_model = OLLAMA_MODEL_CHAT

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API 요청 실패: {str(e)}"
        )

    return ChatResponse(
        message=reply_text,
        model=used_model
    )


@router.get("/health")
def chat_health():
    """Chat 모듈 상태 확인"""
    return {
        "status": "ok",
        "provider": "ollama",
        "base_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL_CHAT,
        "workspace_path": str(WORKSPACE_PATH),
    }
