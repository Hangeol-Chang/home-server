#!/usr/bin/env python3
"""
Home Server API 통합 테스트 스크립트
메인 모듈과 모든 서브모듈의 API 엔드포인트를 테스트합니다.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

class APITester:
    """API 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_request(self, method: str, endpoint: str, data: Dict = None, 
                          expected_status: int = 200, test_name: str = None) -> Dict[str, Any]:
        """API 요청 테스트"""
        url = f"{self.base_url}{endpoint}"
        test_name = test_name or f"{method} {endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    result = await self._process_response(response, expected_status, test_name, start_time)
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    result = await self._process_response(response, expected_status, test_name, start_time)
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data) as response:
                    result = await self._process_response(response, expected_status, test_name, start_time)
            elif method.upper() == "DELETE":
                async with self.session.delete(url) as response:
                    result = await self._process_response(response, expected_status, test_name, start_time)
            else:
                result = {
                    "test_name": test_name,
                    "success": False,
                    "error": f"지원하지 않는 HTTP 메소드: {method}",
                    "response_time": 0
                }
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            result = {
                "test_name": test_name,
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time if 'start_time' in locals() else 0
            }
            self.test_results.append(result)
            return result
    
    async def _process_response(self, response, expected_status, test_name, start_time):
        """응답 처리"""
        response_time = time.time() - start_time
        
        try:
            response_data = await response.json()
        except:
            response_data = await response.text()
        
        success = response.status == expected_status
        
        result = {
            "test_name": test_name,
            "success": success,
            "status_code": response.status,
            "expected_status": expected_status,
            "response_data": response_data,
            "response_time": response_time
        }
        
        if not success:
            result["error"] = f"예상 상태코드 {expected_status}, 실제 {response.status}"
        
        return result
    
    def print_result(self, result: Dict[str, Any]):
        """테스트 결과 출력"""
        status = "✅ 성공" if result["success"] else "❌ 실패"
        print(f"{status} | {result['test_name']} | {result.get('response_time', 0):.3f}s")
        
        if not result["success"]:
            print(f"    오류: {result.get('error', '알 수 없는 오류')}")
        
        if result.get("response_data"):
            # 응답 데이터가 너무 길면 일부만 표시
            data_str = str(result["response_data"])
            if len(data_str) > 200:
                print(f"    응답: {data_str[:200]}...")
            else:
                print(f"    응답: {data_str}")
        print()
    
    def print_summary(self):
        """테스트 요약 출력"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        avg_response_time = sum(result.get("response_time", 0) for result in self.test_results) / total_tests if total_tests > 0 else 0
        
        print("=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"총 테스트: {total_tests}개")
        print(f"성공: {successful_tests}개 ✅")
        print(f"실패: {failed_tests}개 ❌")
        print(f"성공률: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print(f"평균 응답시간: {avg_response_time:.3f}초")
        print("=" * 60)

async def test_main_api(tester: APITester):
    """메인 API 테스트"""
    print("🏠 메인 API 테스트 시작")
    print("-" * 40)
    
    # 루트 엔드포인트
    result = await tester.test_request("GET", "/", test_name="메인 루트")
    tester.print_result(result)
    
    # 헬스 체크
    result = await tester.test_request("GET", "/health", test_name="메인 헬스체크")
    tester.print_result(result)
    
    # API 문서
    result = await tester.test_request("GET", "/docs", expected_status=200, test_name="API 문서")
    tester.print_result(result)

async def test_asset_manager_api(tester: APITester):
    """Asset Manager API 테스트"""
    print("💰 Asset Manager API 테스트 시작")
    print("-" * 40)
    
    # 루트 엔드포인트
    result = await tester.test_request("GET", "/asset-manager/", test_name="Asset Manager 루트")
    tester.print_result(result)
    
    # 헬스 체크
    result = await tester.test_request("GET", "/asset-manager/health", test_name="Asset Manager 헬스체크")
    tester.print_result(result)
    
    # 포트폴리오 조회
    result = await tester.test_request("GET", "/asset-manager/portfolio", test_name="포트폴리오 조회")
    tester.print_result(result)
    
    # 자산 목록 조회
    result = await tester.test_request("GET", "/asset-manager/assets", test_name="자산 목록 조회")
    tester.print_result(result)
    
    # 새 자산 추가
    new_asset = {
        "name": "테스트 주식",
        "type": "stock",
        "value": 500000,
        "currency": "KRW"
    }
    result = await tester.test_request("POST", "/asset-manager/assets", data=new_asset, 
                                     expected_status=200, test_name="새 자산 추가")
    tester.print_result(result)
    
    # 추가된 자산 ID 저장 (업데이트/삭제 테스트용)
    asset_id = None
    if result["success"] and isinstance(result["response_data"], dict):
        asset_id = result["response_data"].get("id")
    
    # 자산 업데이트 (ID가 있는 경우)
    if asset_id:
        updated_asset = {
            "name": "업데이트된 테스트 주식",
            "type": "stock",
            "value": 600000,
            "currency": "KRW"
        }
        result = await tester.test_request("PUT", f"/asset-manager/assets/{asset_id}", 
                                         data=updated_asset, test_name="자산 업데이트")
        tester.print_result(result)
    
    # 가격 동기화
    result = await tester.test_request("POST", "/asset-manager/sync", test_name="가격 동기화")
    tester.print_result(result)
    
    # 월간 보고서 목록
    result = await tester.test_request("GET", "/asset-manager/reports/monthly", test_name="월간 보고서 목록")
    tester.print_result(result)
    
    # 월간 보고서 생성
    result = await tester.test_request("POST", "/asset-manager/reports/generate-monthly", 
                                     test_name="월간 보고서 생성")
    tester.print_result(result)
    
    # 자산 삭제 (ID가 있는 경우)
    if asset_id:
        result = await tester.test_request("DELETE", f"/asset-manager/assets/{asset_id}", 
                                         test_name="자산 삭제")
        tester.print_result(result)

async def test_schedule_manager_api(tester: APITester):
    """Schedule Manager API 테스트"""
    print("📅 Schedule Manager API 테스트 시작")
    print("-" * 40)
    
    # 루트 엔드포인트
    result = await tester.test_request("GET", "/schedule-manager/", test_name="Schedule Manager 루트")
    tester.print_result(result)
    
    # 헬스 체크
    result = await tester.test_request("GET", "/schedule-manager/health", test_name="Schedule Manager 헬스체크")
    tester.print_result(result)
    
    # 작업 목록 조회
    result = await tester.test_request("GET", "/schedule-manager/tasks", test_name="작업 목록 조회")
    tester.print_result(result)
    
    # 새 작업 생성
    new_task = {
        "name": "테스트 작업",
        "description": "API 테스트용 작업",
        "task_type": "once",
        "scheduled_time": "2025-10-10T09:00:00",
        "command": "test_command",
        "parameters": {"test_param": "test_value"}
    }
    result = await tester.test_request("POST", "/schedule-manager/tasks", data=new_task,
                                     test_name="새 작업 생성")
    tester.print_result(result)
    
    # 생성된 작업 ID 저장
    task_id = None
    if result["success"] and isinstance(result["response_data"], dict):
        task_id = result["response_data"].get("id")
    
    # 특정 작업 조회 (ID가 있는 경우)
    if task_id:
        result = await tester.test_request("GET", f"/schedule-manager/tasks/{task_id}", 
                                         test_name="특정 작업 조회")
        tester.print_result(result)
    
    # 실행 기록 조회
    result = await tester.test_request("GET", "/schedule-manager/executions", test_name="실행 기록 조회")
    tester.print_result(result)
    
    # 통계 조회
    result = await tester.test_request("GET", "/schedule-manager/stats", test_name="통계 조회")
    tester.print_result(result)
    
    # 작업 즉시 실행 (ID가 있는 경우)
    if task_id:
        result = await tester.test_request("POST", f"/schedule-manager/tasks/{task_id}/execute", 
                                         test_name="작업 즉시 실행")
        tester.print_result(result)
    
    # 작업 삭제 (ID가 있는 경우)
    if task_id:
        result = await tester.test_request("DELETE", f"/schedule-manager/tasks/{task_id}", 
                                         test_name="작업 삭제")
        tester.print_result(result)

async def check_server_status(base_url: str) -> bool:
    """서버 상태 확인"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
    except:
        return False

async def main():
    """메인 테스트 함수"""
    print("🧪 Home Server API 통합 테스트")
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 서버 상태 확인
    print("🔍 서버 연결 확인 중...")
    if not await check_server_status(base_url):
        print("❌ 서버에 연결할 수 없습니다.")
        print("다음 명령으로 서버를 먼저 실행해주세요:")
        print("cd /home/hg/workspace/home-server/main/app")
        print("source ../../.venv/bin/activate")
        print("python3 main.py")
        return
    
    print("✅ 서버 연결 확인됨")
    print()
    
    # API 테스트 실행
    async with APITester(base_url) as tester:
        # 메인 API 테스트
        await test_main_api(tester)
        
        # Asset Manager API 테스트
        await test_asset_manager_api(tester)
        
        # Schedule Manager API 테스트  
        await test_schedule_manager_api(tester)
        
        # 전체 결과 요약
        tester.print_summary()
        
        # 실패한 테스트 상세 정보
        failed_tests = [result for result in tester.test_results if not result["success"]]
        if failed_tests:
            print("\n🔍 실패한 테스트 상세 정보:")
            print("-" * 40)
            for i, result in enumerate(failed_tests, 1):
                print(f"{i}. {result['test_name']}")
                print(f"   오류: {result.get('error', '알 수 없는 오류')}")
                if result.get('status_code'):
                    print(f"   상태코드: {result['status_code']} (예상: {result.get('expected_status')})")
                print()
    
    print(f"테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # 필요한 패키지 확인
    try:
        import aiohttp
    except ImportError:
        print("❌ aiohttp 패키지가 필요합니다.")
        print("다음 명령으로 설치해주세요: pip install aiohttp")
        sys.exit(1)
    
    # 비동기 테스트 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ 테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()