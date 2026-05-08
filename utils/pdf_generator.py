"""
PDF Generator - Medical Report Generation
Creates comprehensive PDF reports with medication information and pharmacy details
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.colors import HexColor, black, white, lightgrey
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
except ImportError:
    print("Warning: reportlab not installed. PDF generation will be limited.")
    SimpleDocTemplate = None

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate comprehensive medical prescription reports in PDF format"""

    def __init__(self, output_dir: str = "./pharma_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet() if SimpleDocTemplate else None
        self._setup_custom_styles()

        logger.info(f"PDFReportGenerator initialized with output dir: {output_dir}")

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        if not self.styles:
            return

        # Title style
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=self.styles["Heading1"],
            fontSize=20,
            textColor=HexColor("#1a5490"),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold"
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=14,
            textColor=HexColor("#2e7bb4"),
            spaceAfter=8,
            spaceBefore=8,
            fontName="Helvetica-Bold"
        ))

        # Normal text style
        self.styles.add(ParagraphStyle(
            name="MedicalText",
            parent=self.styles["BodyText"],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName="Helvetica"
        ))

    def generate_report(
        self,
        patient_info: Dict,
        medications: List[Dict],
        pharmacies: List[Dict],
        warnings: List[str],
        drug_images: Dict[str, Optional[str]] = None,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate comprehensive PDF report

        Args:
            patient_info: Patient data {name, age, sex, diagnosis}
            medications: List of medication info
            pharmacies: List of nearby pharmacies
            warnings: List of warning messages
            drug_images: Dictionary of drug names to image paths
            filename: Output filename (auto-generated if None)

        Returns:
            Path to generated PDF or None
        """
        if not SimpleDocTemplate:
            logger.error("reportlab not installed")
            return None

        try:
            # Generate filename if not provided
            if not filename:
                patient_name = patient_info.get("name", "patient").replace(" ", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"pharma_report_{patient_name}_{timestamp}.pdf"

            filepath = os.path.join(self.output_dir, filename)

            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []

            # Add title
            story.append(Paragraph("의료 처방약 분석 보고서", self.styles["ReportTitle"]))
            story.append(Spacer(1, 0.3*inch))

            # Add patient information section
            story.extend(self._build_patient_section(patient_info))

            # Add medications section
            story.extend(self._build_medications_section(medications, drug_images))

            # Add pharmacy section
            story.extend(self._build_pharmacy_section(pharmacies))

            # Add warnings section
            if warnings:
                story.extend(self._build_warnings_section(warnings))

            # Add footer
            story.extend(self._build_footer())

            # Build PDF
            doc.build(story)

            logger.info(f"PDF report generated: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return None

    def _build_patient_section(self, patient_info: Dict) -> List:
        """Build patient information section"""
        elements = []

        elements.append(Paragraph("【환자 정보】", self.styles["SectionHeader"]))

        # Patient info table
        patient_data = [
            ["이름", patient_info.get("name", "")],
            ["나이/성별", f"{patient_info.get('age', '')}세 / {patient_info.get('sex', '')}"],
            ["주진료", patient_info.get("primary_diagnosis", "")],
            ["부진료", patient_info.get("secondary_diagnosis", "")],
            ["처방일", patient_info.get("prescription_date", "")]
        ]

        table = Table(patient_data, colWidths=[2*cm, 12*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#e8f0f7")),
            ("TEXTCOLOR", (0, 0), (-1, -1), black),
            ("ALIGN", (0, 0), (-1, -1), TA_LEFT),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_medications_section(self, medications: List[Dict], drug_images: Dict = None) -> List:
        """Build medications section"""
        elements = []

        elements.append(Paragraph("【처방약물 정보】", self.styles["SectionHeader"]))

        for idx, med in enumerate(medications, 1):
            # Medication header
            med_title = f"{idx}. {med.get('name', '')} ({med.get('strength', '')})"
            elements.append(Paragraph(med_title, self.styles["Heading3"]))

            # Medication details table
            med_data = [
                ["1일 권장량", med.get("daily_dose", "")],
                ["투여 횟수", med.get("frequency", "")],
                ["투약 기간", med.get("duration", "")],
                ["약가", f"{med.get('price', '')}원"],
                ["주의사항", med.get("warnings", "")],
                ["상호작용", med.get("interactions", "")]
            ]

            table = Table(med_data, colWidths=[3*cm, 11*cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), HexColor("#f5f5f5")),
                ("ALIGN", (0, 0), (-1, -1), TA_LEFT),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 1, lightgrey)
            ]))

            elements.append(table)

            # Add medication image if available
            if drug_images and med.get("name") in drug_images:
                image_path = drug_images[med.get("name")]
                if image_path and os.path.exists(image_path):
                    try:
                        img = Image(image_path, width=2*cm, height=2*cm)
                        elements.append(img)
                    except Exception as e:
                        logger.warning(f"Could not add image: {e}")

            elements.append(Spacer(1, 0.2*inch))

            # Page break if needed
            if idx % 3 == 0:
                elements.append(PageBreak())

        return elements

    def _build_pharmacy_section(self, pharmacies: List[Dict]) -> List:
        """Build pharmacy information section"""
        elements = []

        elements.append(Paragraph("【근처 약국 정보】", self.styles["SectionHeader"]))

        if not pharmacies:
            elements.append(Paragraph("약국 정보를 찾을 수 없습니다.", self.styles["MedicalText"]))
            return elements

        # Pharmacy table header
        pharmacy_data = [
            ["약국명", "거리", "전화", "영업시간", "공시약가"]
        ]

        for pharmacy in pharmacies[:5]:  # Limit to top 5
            row = [
                pharmacy.get("name", ""),
                f"{pharmacy.get('distance_km', 0):.1f}km",
                pharmacy.get("phone", ""),
                pharmacy.get("hours", ""),
                pharmacy.get("mfds_price", "")
            ]
            pharmacy_data.append(row)

        table = Table(pharmacy_data, colWidths=[3*cm, 1.5*cm, 2.5*cm, 3*cm, 2*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2e7bb4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("ALIGN", (0, 0), (-1, -1), TA_LEFT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, black),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f0f0f0")])
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))

        return elements

    def _build_warnings_section(self, warnings: List[str]) -> List:
        """Build warnings section"""
        elements = []

        elements.append(Paragraph("【주의 사항】", self.styles["SectionHeader"]))

        for warning in warnings:
            warning_text = f"• {warning}"
            elements.append(Paragraph(warning_text, self.styles["MedicalText"]))

        elements.append(Spacer(1, 0.2*inch))

        return elements

    def _build_footer(self) -> List:
        """Build footer section"""
        elements = []

        footer_text = f"""
        <font size=9>
        생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}<br/>
        본 보고서는 의료 정보 제공 목적으로만 작성되었습니다.<br/>
        약물 복용 및 건강 관련 결정은 반드시 의료 전문가와 상담하십시오.
        </font>
        """

        elements.append(Paragraph(footer_text, self.styles["Normal"]))

        return elements

    def generate_html_report(
        self,
        patient_info: Dict,
        medications: List[Dict],
        pharmacies: List[Dict],
        warnings: List[str],
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate HTML report (alternative to PDF)

        Args:
            patient_info: Patient data
            medications: List of medications
            pharmacies: List of pharmacies
            warnings: List of warnings
            filename: Output filename

        Returns:
            Path to generated HTML file
        """
        try:
            if not filename:
                patient_name = patient_info.get("name", "patient").replace(" ", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"pharma_report_{patient_name}_{timestamp}.html"

            filepath = os.path.join(self.output_dir, filename)

            html_content = self._build_html_content(
                patient_info, medications, pharmacies, warnings
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(f"HTML report generated: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return None

    def _build_html_content(self, patient_info, medications, pharmacies, warnings) -> str:
        """Build HTML content"""
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>의료 처방약 분석 보고서</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; }}
                .header {{ text-align: center; color: #1a5490; border-bottom: 2px solid #2e7bb4; padding-bottom: 20px; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ font-size: 18px; font-weight: bold; color: #2e7bb4; border-left: 4px solid #2e7bb4; padding-left: 10px; margin-top: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background-color: #2e7bb4; color: white; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .warning {{ color: #d32f2f; padding: 10px; background-color: #ffebee; border-left: 4px solid #d32f2f; margin: 10px 0; }}
                .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 12px; border-top: 1px solid #ddd; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>의료 처방약 분석 보고서</h1>
            </div>

            <div class="section">
                <div class="section-title">【환자 정보】</div>
                <table>
                    <tr><th>이름</th><td>{patient_info.get('name', '')}</td></tr>
                    <tr><th>나이/성별</th><td>{patient_info.get('age', '')}세 / {patient_info.get('sex', '')}</td></tr>
                    <tr><th>주진료</th><td>{patient_info.get('primary_diagnosis', '')}</td></tr>
                    <tr><th>부진료</th><td>{patient_info.get('secondary_diagnosis', '')}</td></tr>
                    <tr><th>처방일</th><td>{patient_info.get('prescription_date', '')}</td></tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">【처방약물 정보】</div>
        """

        for idx, med in enumerate(medications, 1):
            html += f"""
                <h3>{idx}. {med.get('name', '')} ({med.get('strength', '')})</h3>
                <table>
                    <tr><th>1일 권장량</th><td>{med.get('daily_dose', '')}</td></tr>
                    <tr><th>투여 횟수</th><td>{med.get('frequency', '')}</td></tr>
                    <tr><th>투약 기간</th><td>{med.get('duration', '')}</td></tr>
                    <tr><th>약가</th><td>{med.get('price', '')}원</td></tr>
                    <tr><th>주의사항</th><td>{med.get('warnings', '')}</td></tr>
                </table>
            """

        html += """
            </div>

            <div class="section">
                <div class="section-title">【근처 약국 정보】</div>
                <table>
                    <tr>
                        <th>약국명</th>
                        <th>거리</th>
                        <th>전화</th>
                        <th>영업시간</th>
                        <th>공시약가</th>
                    </tr>
        """

        for pharmacy in pharmacies[:5]:
            html += f"""
                    <tr>
                        <td>{pharmacy.get('name', '')}</td>
                        <td>{pharmacy.get('distance_km', 0):.1f}km</td>
                        <td>{pharmacy.get('phone', '')}</td>
                        <td>{pharmacy.get('hours', '')}</td>
                        <td>{pharmacy.get('mfds_price', '')}</td>
                    </tr>
            """

        html += """
                </table>
            </div>
        """

        if warnings:
            html += """
            <div class="section">
                <div class="section-title">【주의 사항】</div>
            """
            for warning in warnings:
                html += f'<div class="warning">• {warning}</div>'
            html += "</div>"

        html += f"""
            <div class="footer">
                <p>생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
                <p>본 보고서는 의료 정보 제공 목적으로만 작성되었습니다.<br/>
                약물 복용 및 건강 관련 결정은 반드시 의료 전문가와 상담하십시오.</p>
            </div>
        </body>
        </html>
        """

        return html


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    generator = PDFReportGenerator()

    # Example usage
    patient = {
        "name": "김철수",
        "age": 68,
        "sex": "남성",
        "primary_diagnosis": "고혈압",
        "secondary_diagnosis": "당뇨병",
        "prescription_date": "2024-05-07"
    }

    medications = [
        {
            "name": "노바스크정",
            "strength": "5mg",
            "daily_dose": "1회 1정 (5mg)",
            "frequency": "1일 1회 (아침)",
            "duration": "30일",
            "price": 1123,
            "warnings": "자몽 주스와 함께 섭취 금지"
        }
    ]

    pharmacies = [
        {
            "name": "서울약국",
            "distance_km": 0.5,
            "phone": "02-123-4567",
            "hours": "9:00~22:00",
            "mfds_price": "1,123원"
        }
    ]

    warnings = ["고령자 저혈압 주의", "정기적 검사 필요"]

    # Generate HTML report
    html_path = generator.generate_html_report(patient, medications, pharmacies, warnings)
    print(f"HTML report generated: {html_path}")
