#!/usr/bin/env python3
"""
Home Server API 간단 테스트 스크립트 (동기 버전)
requests 라이브러리를 사용하여 API 엔드포인트를 테스트합니다.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

class SimpleAPITester:
    """간단한 API 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_request(self, method: str, endpoint: str, data: Dict = None, 
                    expected_status: int = 200, test_name: str = None) -> Dict[str, Any]:
        """API 요청 테스트"""
        url = f"{self.base_url}{endpoint}"
        test_name = test_name or f"{method} {endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=10)
            else:
                result = {
                    "test_name": test_name,
                    "success": False,
                    "error": f"지원하지 않는 HTTP 메소드: {method}",
                    "response_time": 0
                }
                self.test_results.append(result)
                return result
            
            response_time = time.time() - start_time
            
            # 응답 데이터 파싱
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            success = response.status_code == expected_status
            
            result = {
                "test_name": test_name,
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_data": response_data,
                "response_time": response_time
            }
            
            if not success:
                result["error"] = f"예상 상태코드 {expected_status}, 실제 {response.status_code}"
            
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
    
    def print_result(self, result: Dict[str, Any]):
        """테스트 결과 출력"""
        status = "✅ 성공" if result["success"] else "❌ 실패"
        print(f"{status} | {result['test_name']} | {result.get('response_time', 0):.3f}s")
        
        if not result["success"]:
            print(f"    오류: {result.get('error', '알 수 없는 오류')}")
        
        if result.get("response_data") and result["success"]:
            # 성공한 경우 응답의 주요 정보만 표시
            data = result["response_data"]
            if isinstance(data, dict):
                if "service" in data:
                    print(f"    서비스: {data['service']}")
                if "total_assets" in data:
                    print(f"    총 자산: {data['total_assets']}개")
                if "total_value" in data:
                    print(f"    총 가치: {data['total_value']:,.0f}")
                if "message" in data:
                    print(f"    메시지: {data['message']}")
                if "name" in data and "id" in data:
                    print(f"    생성됨: {data['name']} (ID: {data['id']})")
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

def test_main_endpoints(tester: SimpleAPITester):
    """메인 엔드포인트 테스트"""
    print("🏠 메인 API 테스트")
    print("-" * 30)
    
    # 기본 테스트들
    result = tester.test_request("GET", "/", test_name="메인 루트")
    tester.print_result(result)
    
    result = tester.test_request("GET", "/health", test_name="헬스체크")
    tester.print_result(result)

def test_asset_manager(tester: SimpleAPITester):
    """Asset Manager 테스트"""
    print("💰 Asset Manager 테스트")
    print("-" * 30)
    
    # 기본 엔드포인트
    result = tester.test_request("GET", "/asset-manager/", test_name="Asset Manager 루트")
    tester.print_result(result)
    
    result = tester.test_request("GET", "/asset-manager/health", test_name="헬스체크")
    tester.print_result(result)
    
    result = tester.test_request("GET", "/asset-manager/portfolio", test_name="포트폴리오 조회")
    tester.print_result(result)
    
    # 새 자산 추가 테스트
    new_asset = {
        "name": "테스트 코인",
        "type": "crypto", 
        "value": 1000000,
        "currency": "KRW"
    }
    result = tester.test_request("POST", "/asset-manager/assets", data=new_asset, test_name="자산 추가")
    tester.print_result(result)
    
    # 월간 보고서 생성 테스트
    result = tester.test_request("POST", "/asset-manager/reports/generate-monthly", test_name="월간 보고서 생성")
    tester.print_result(result)

def test_schedule_manager(tester: SimpleAPITester):
    """Schedule Manager 테스트"""
    print("📅 Schedule Manager 테스트")
    print("-" * 30)
    
    result = tester.test_request("GET", "/schedule-manager/", test_name="Schedule Manager 루트")
    tester.print_result(result)
    
    result = tester.test_request("GET", "/schedule-manager/health", test_name="헬스체크")
    tester.print_result(result)
    
    result = tester.test_request("GET", "/schedule-manager/tasks", test_name="작업 목록")
    tester.print_result(result)
    
    # 새 작업 생성 테스트
    new_task = {
        "name": "간단 테스트 작업",
        "task_type": "once",
        "scheduled_time": "2025-10-10T10:00:00",
        "command": "test_simple"
    }
    result = tester.test_request("POST", "/schedule-manager/tasks", data=new_task, test_name="작업 생성")
    tester.print_result(result)
    
    result = tester.test_request("GET", "/schedule-manager/stats", test_name="통계 조회")
    tester.print_result(result)

def check_server_simple(base_url: str) -> bool:
    """서버 상태 간단 확인"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """메인 함수"""
    print("🧪 Home Server API 간단 테스트")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 서버 연결 확인
    print("🔍 서버 연결 확인...")
    if not check_server_simple(base_url):
        print("❌ 서버에 연결할 수 없습니다!")
        print("\n서버 실행 방법:")
        print("1. cd /home/hg/workspace/home-server/main/app")
        print("2. source ../../.venv/bin/activate")
        print("3. python3 main.py")
        return
    
    print("✅ 서버 연결됨\n")
    
    # 테스트 실행
    tester = SimpleAPITester(base_url)
    
    try:
        # 각 모듈별 테스트
        test_main_endpoints(tester)
        test_asset_manager(tester)
        test_schedule_manager(tester)
        
        # 결과 요약
        tester.print_summary()
        
        # 실패 테스트가 있으면 상세 정보 출력
        failed_tests = [r for r in tester.test_results if not r["success"]]
        if failed_tests:
            print("\n❌ 실패한 테스트:")
            for result in failed_tests:
                print(f"  • {result['test_name']}: {result.get('error', '알 수 없는 오류')}")
        else:
            print("\n🎉 모든 테스트가 성공했습니다!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 테스트 중단됨")
    except Exception as e:
        print(f"\n\n❌ 테스트 오류: {e}")
    
    print(f"\n테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # requests 패키지 확인
    try:
        import requests
    except ImportError:
        print("❌ requests 패키지가 필요합니다.")
        print("설치 명령: pip install requests")
        exit(1)
    
    main()