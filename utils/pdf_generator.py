"""
PDF Generator - 처방약 정보 보고서 생성
"""
from typing import Dict, List, Optional
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class PrescriptionReportGenerator:
    """처방약 정보 보고서 생성"""
    
    def generate_html_report(self, prescription_data: Dict, medication_info: Dict, 
                            pharmacy_data: List[Dict], output_path: str) -> bool:
        """HTML 형식 보고서 생성"""
        try:
            html = self._generate_html(prescription_data, medication_info, pharmacy_data)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"HTML 보고서 생성 완료: {output_path}")
            return True
        except Exception as e:
            logger.error(f"HTML 보고서 생성 실패: {str(e)}")
            return False
    
    @staticmethod
    def _generate_html(prescription_data: Dict, medication_info: Dict, 
                      pharmacy_data: List[Dict]) -> str:
        """HTML 보고서 생성"""
        patient = prescription_data.get('patient', {})
        diagnosis = prescription_data.get('diagnosis', {})
        medications = prescription_data.get('medications', [])
        
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>처방약 정보 보고서</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
        h1 {{ color: #667eea; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
    </style>
</head>
<body>
    <h1>💊 처방약 정보 보고서</h1>
    <p>생성일: {datetime.now().strftime('%Y년 %m월 %d일')}</p>
    
    <div class="section">
        <h2>환자 정보</h2>
        <p>성명: {patient.get('name', 'N/A')} | 나이: {patient.get('age', 'N/A')}세</p>
    </div>
</body>
</html>
"""
        return html
