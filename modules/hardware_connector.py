"""
30년 베테랑 선배님 지시사항: 조제기 하드웨어 연동 모듈 (PLC / REST API)
작성자: 보조 아키텍처 (학습 중)

이 모듈은 자동 조제기기(ATC, Automatic Tablet Dispenser) 하드웨어와 통신하기 위한 
REST API 커넥터와 PLC(Programmable Logic Controller / Power Line Communication) 제어 인터페이스를 포함합니다.
"""

import logging
import json
import requests
from typing import Dict, Any, List

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DispensingMachineAPIConnector:
    """REST API 기반 최신 조제기 통신 커넥터"""
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def check_status(self) -> Dict[str, Any]:
        """조제기 현재 상태 확인"""
        try:
            logger.info("선배님, 조제기 상태를 확인 중입니다...")
            response = requests.get(f"{self.base_url}/api/v1/status", headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"조제기 상태 확인 실패: {e}")
            return {"status": "error", "message": str(e)}

    def dispense_prescription(self, prescription_id: str, medications: List[Dict[str, Any]]) -> bool:
        """처방전 데이터 전송 및 조제 명령"""
        payload = {
            "prescription_id": prescription_id,
            "medications": medications
        }
        try:
            logger.info(f"선배님, 처방전({prescription_id}) 조제 명령을 API로 전송합니다.")
            response = requests.post(f"{self.base_url}/api/v1/dispense", headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("조제 명령 전송 성공!")
            return True
        except requests.RequestException as e:
            logger.error(f"조제 명령 전송 실패: {e}")
            return False

class DispensingMachinePLCConnector:
    """
    구형/산업용 조제기 하드웨어 직접 제어 모듈 (PLC 통신 - TCP/IP 또는 Serial)
    (예: Modbus TCP, LS산전/Mitsubishi PLC 프로토콜)
    """
    def __init__(self, ip_address: str, port: int = 502):
        self.ip_address = ip_address
        self.port = port
        self.connected = False
        # 실제 구현시 pymodbus.client.sync.ModbusTcpClient 등 활용
        # self.client = ModbusTcpClient(self.ip_address, port=self.port)
        
    def connect(self) -> bool:
        """PLC 장비와 연결 시도"""
        logger.info(f"선배님, PLC 기기({self.ip_address}:{self.port})와 TCP/IP 연결을 시도합니다.")
        # self.connected = self.client.connect()
        self.connected = True  # Mock
        if self.connected:
            logger.info("PLC 기계 통신 포트 오픈 및 연결 성공했습니다!")
        return self.connected

    def trigger_dispense(self, canister_id: int, quantity: int) -> bool:
        """
        특정 캐니스터(약통)에서 지정된 수량의 알약 배출 제어
        """
        if not self.connected:
            logger.warning("PLC가 연결되지 않았습니다. 먼저 connect()를 호출해주세요.")
            return False
            
        logger.info(f"선배님, 지시하신 대로 {canister_id}번 약통에서 {quantity}알 배출 PLC 펄스 신호를 전송합니다.")
        # 실제 PLC 메모리 맵(주소)에 값을 쓰는 로직 (예: 코일 또는 레지스터 쓰기)
        # self.client.write_register(address=100, value=canister_id)
        # self.client.write_register(address=101, value=quantity)
        # trigger_signal = self.client.write_coil(address=10, value=True)
        return True

    def disconnect(self):
        """PLC 장비 연결 해제"""
        if self.connected:
            logger.info("PLC 장비와의 연결을 안전하게 해제합니다. 오늘도 수고하셨습니다 선배님!")
            # self.client.close()
            self.connected = False

if __name__ == "__main__":
    # 선배님께 테스트 결과 시연
    print("\n==================================")
    print(" [최신형 REST API 조제기 시연] ")
    print("==================================")
    api_hw = DispensingMachineAPIConnector("http://192.168.1.100:8080", "secret_key_123")
    api_hw.check_status()
    api_hw.dispense_prescription("RX-20231024-01", [{"code": "A11", "qty": 3}, {"code": "B22", "qty": 1}])
    
    print("\n===================================")
    print(" [구형 산업용 PLC 조제기 제어 시연] ")
    print("===================================")
    plc_hw = DispensingMachinePLCConnector("192.168.1.101", 502)
    plc_hw.connect()
    plc_hw.trigger_dispense(canister_id=45, quantity=2)
    plc_hw.disconnect()
