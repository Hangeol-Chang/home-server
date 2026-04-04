from fastapi import APIRouter, HTTPException, status
import os
import requests

router = APIRouter(
    prefix="/test",
    tags=["Test Modules"],
    responses={404: {"description": "Not found"}}
)

@router.post("/discord-webhook")
def check_discord_webhook():
    """
    디스코드 웹훅의 정상 작동 여부를 테스트합니다.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url or webhook_url == "여기에_웹훅_주소를_입력해주세요":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DISCORD_WEBHOOK_URL 환경 변수가 올바르게 설정되지 않았습니다."
        )

    discord_payload = {
        "username": "AI 재무비서 (Test)",
        "content": "✅ **시스템 테스트 성공!**\n이 메시지는 서버의 웹훅 테스트 페이지에서 전송되었습니다."
    }

    try:
        response = requests.post(webhook_url, json=discord_payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discord Webhook 전송 실패: {str(e)}"
        )

    return {"message": "디스코드 테스트 메시지를 성공적으로 전송했습니다.", "status": "success"}
