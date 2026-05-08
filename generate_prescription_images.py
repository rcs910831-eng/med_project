import os
import re
from PIL import Image, ImageDraw, ImageFont
import json
import importlib.util
import sys

# 폰트 설정 (윈도우 기본 맑은 고딕)
FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/malgunbd.ttf"

def create_prescription_image(patient_data, output_path):
    width, height = 800, 1100
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 46)
        font_header = ImageFont.truetype(FONT_BOLD_PATH, 24)
        font_text = ImageFont.truetype(FONT_PATH, 18)
        font_small = ImageFont.truetype(FONT_PATH, 14)
        font_warn_hdr = ImageFont.truetype(FONT_BOLD_PATH, 20)
        font_warn_item = ImageFont.truetype(FONT_BOLD_PATH, 16)
        font_warn_sub = ImageFont.truetype(FONT_PATH, 15)
    except:
        font_title = font_header = font_text = font_small = font_warn_hdr = font_warn_item = font_warn_sub = ImageFont.load_default()

    # 1. 배경 디자인 (상단 바 및 테두리)
    draw.rectangle([0, 0, width, 20], fill="#1e3a8a")
    draw.rectangle([10, 10, 790, 1090], outline="#1e3a8a", width=3)
    
    # 2. 타이틀 영역
    draw.text((width//2 - 80, 50), "처 방 전", font=font_title, fill='#1e3a8a')
    draw.line([(50, 105), (750, 105)], fill="#1e3a8a", width=2)
    draw.text((600, 40), f"교부번호: {patient_data['pid']}-2026", font=font_small, fill='#64748b')

    # 진단명 그대로 보존 (논문/차트 형식 유지)
    disease = patient_data['disease'].replace(",", " / ")

    # 3. 환자 정보 섹션 (더 깔끔하게)
    draw.rectangle([50, 120, 750, 240], outline="#cbd5e1", width=1)
    draw.rectangle([50, 120, 200, 240], fill="#f8fafc")
    
    labels = ["환 자 명", "처방의사", "주진단명", "처방일자"]
    vals = [patient_data['name'], patient_data['doctor'], disease, patient_data['date']]
    
    for i in range(2):
        # 상단 2개 (환자명, 의사)
        draw.text((70, 140 + i*60), labels[i], font=font_header, fill='#1e3a8a')
        draw.text((220, 140 + i*60), vals[i], font=font_header, fill='#0f172a')
        # 하단 2개 (병명, 일자)
        draw.text((440, 140 + i*60), labels[i+2], font=font_text, fill='#64748b')
        draw.text((540, 140 + i*60), vals[i+2], font=font_text, fill='#0f172a')

    # 4. 처방 내역 헤더
    header_y = 260
    draw.rectangle([50, header_y, 750, header_y+40], fill="#334155")
    draw.text((70, header_y+10), "처방 의약품 및 복용법", font=font_text, fill='white')
    draw.text((450, header_y+10), "1회/1일", font=font_text, fill='white')
    draw.text((650, header_y+10), "총일수", font=font_text, fill='white')

    # 5. 약품 내역 리스트업
    meds = [m.strip() for m in patient_data['meds'].split(",")]
    dosages = [d.strip() for d in patient_data['dosage'].split(",")]
    freqs = [f.strip() for f in patient_data['freq'].split(",")]
    
    y_offset = 310
    for i in range(len(meds)):
        if y_offset > 750: break
        
        med = meds[i]
        dosage = dosages[i] if i < len(dosages) else "1"
        freq = freqs[i] if i < len(freqs) else "1일 3회"
        
        # 행 배경 (교차 색상)
        if i % 2 == 0:
            draw.rectangle([50, y_offset, 750, y_offset+40], fill="#f1f5f9")
        
        # 텍스트
        med_display = med.replace("[주]", "🔵").replace("[부]", "🟢")
        draw.text((60, y_offset+10), med_display, font=font_text, fill='#0f172a')
        draw.text((460, y_offset+10), f"{dosage} / {freq}", font=font_text, fill='#0f172a')
        draw.text((670, y_offset+10), patient_data['duration'], font=font_text, fill='#0f172a')
        
        y_offset += 42

    # 6. 정밀 복약지도 및 주의사항 (가장 중요한 부분 - 깔끔하게 변경)
    y_warn_box = 780
    draw.rectangle([50, y_warn_box, 750, 1050], outline="#dc2626", width=2)
    draw.rectangle([50, y_warn_box, 750, y_warn_box+40], fill="#fee2e2")
    draw.text((65, y_warn_box+10), "🚨 임상 필수 주의사항 및 복약 수칙 (사령관 지시)", font=font_warn_hdr, fill='#991b1b')
    
    warnings = patient_data.get('warnings_list', [])
    if not warnings:
        warnings = ["정해진 용법과 용량을 엄격히 준수하십시오."]
    
    curr_y = y_warn_box + 55
    for idx, warn in enumerate(warnings[:7]): # 최대 7개
        # 아이콘 (체크박스 스타일)
        draw.rectangle([70, curr_y+2, 85, curr_y+17], outline="#991b1b", width=2)
        draw.line([(72, curr_y+10), (76, curr_y+14), (82, curr_y+5)], fill="#991b1b", width=2)
        
        # 텍스트
        text = str(warn).strip()
        if len(text) > 50: text = text[:47] + "..."
        
        # 강조 색상
        text_color = '#991b1b' if any(w in text for w in ["주의", "금지", "경고", "위험", "중단"]) else '#1e293b'
        draw.text((100, curr_y), text, font=font_warn_item, fill=text_color)
        curr_y += 35

    # 7. 하단 로고 및 워터마크
    draw.text((width//2 - 120, 1065), "PHARMA-HYBRID STRATEGIC CLINICAL SYSTEM", font=font_small, fill='#94a3b8')

    img.save(output_path)
    return output_path

if __name__ == "__main__":
    # Import RAW_RX and DEFAULT_PATIENTS from main script
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from 전부_코드화_데이터통합시스템 import RAW_RX, PILL_KB, DEFAULT_PATIENTS
    except ImportError:
        # Fallback if import fails
        RAW_RX = []
        PILL_KB = {}
        DEFAULT_PATIENTS = {}

    output_dir = "prescription_images"
    os.makedirs(output_dir, exist_ok=True)

    # 1. 환자별 데이터 그룹화
    patient_groups = {}
    for rx in RAW_RX:
        pid = rx[1]
        if pid not in patient_groups:
            patient_groups[pid] = []
        patient_groups[pid].append(rx)

    count = 0
    # 모든 환자(DEFAULT_PATIENTS)에 대해 이미지 생성 시도
    for pid in DEFAULT_PATIENTS.keys():
        rxs = patient_groups.get(pid, [])
        
        # 한 환자의 모든 약물과 진단명을 통합
        all_meds = []
        all_dosages = []
        all_freqs = []
        all_diagnoses = []
        all_warnings = []
        
        # 기본 정보
        pat_info = DEFAULT_PATIENTS[pid]
        pat_name = pat_info.get("real_name", f"환자_{pid}")
        
        if rxs:
            main_doc = rxs[0][8]
            main_date = rxs[0][7]
            main_duration = rxs[0][6]

            for rx in rxs:
                diag = rx[3]
                if diag not in all_diagnoses:
                    all_diagnoses.append(diag)
                
                meds_list = [m.strip() for m in rx[2].split(",")]
                dose_list = [d.strip() for d in rx[4].split(",")]
                freq_list = [f.strip() for f in rx[5].split(",")]
                
                for i in range(len(meds_list)):
                    prefix = "[주]" if "주진단" in diag else "[부]"
                    all_meds.append(f"{prefix} {meds_list[i]}")
                    all_dosages.append(dose_list[i] if i < len(dose_list) else "1정")
                    all_freqs.append(freq_list[i] if i < len(freq_list) else "1일 3회")

                for m in meds_list:
                    # 약물명 정규화
                    clean_m = re.sub(r'\(.*\)', '', m).strip()
                    clean_m = re.sub(r'\d+m[gc].*', '', clean_m).strip()
                    
                    # 1. PILL_KB (상세 데이터베이스)
                    kb_info = PILL_KB.get(m) or PILL_KB.get(clean_m)
                    if not kb_info:
                        for k, v in PILL_KB.items():
                            if k in m or clean_m in k:
                                kb_info = v
                                break
                    
                    if kb_info:
                        if 'warnings' in kb_info: all_warnings.extend(kb_info['warnings'])
                        elif 'side_effects' in kb_info: all_warnings.extend(kb_info['side_effects'])
                        if 'caution' in kb_info: all_warnings.append(kb_info['caution'])
                        if 'efficacy' in kb_info: all_warnings.append(f"효능: {kb_info['efficacy']}")

                    # 2. KB["약물"] (논문 기반 데이터베이스)
                    try:
                        from 전부_코드화_데이터통합시스템 import KB
                        paper_info = KB["약물"].get(m) or KB["약물"].get(clean_m)
                        if paper_info:
                            if '주의' in paper_info: all_warnings.append(f"[임상주의] {paper_info['주의']}")
                            if '부작용' in paper_info: all_warnings.append(f"[부작용] {paper_info['부작용']}")
                            if '근거' in paper_info: all_warnings.append(f"[학술근거] {paper_info['근거']}")
                    except:
                        pass
        else:
            # 처방전이 없는 환자용 더미 데이터
            main_doc = "담당의 지정전"
            main_date = "2026-05-06"
            main_duration = "N/A"
            all_meds = ["현재 활성 처방 내역이 없습니다."]
            all_diagnoses = ["건강검진 및 모니터링 대상"]
            all_dosages = ["-"]
            all_freqs = ["-"]
            all_warnings = ["정기 검진 일정을 확인하십시오.", "불편 증상 발생 시 내원 바랍니다."]

        unique_warnings = list(dict.fromkeys(all_warnings))
        
        patient_data = {
            "pid": pid,
            "name": pat_name,
            "meds": ", ".join(all_meds),
            "disease": ", ".join(all_diagnoses),
            "dosage": ", ".join(all_dosages),
            "freq": ", ".join(all_freqs),
            "duration": main_duration,
            "date": main_date,
            "doctor": main_doc,
            "warnings_list": unique_warnings if unique_warnings else ["복용 전 전문가와 상담하십시오."]
        }
        
        out_path = os.path.join(output_dir, f"RX_{pid}.png")
        create_prescription_image(patient_data, out_path)
        count += 1
    
    print(f"Success: Generated {count} prescription images for ALL personnel.")


