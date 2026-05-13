#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
drug_info_complete_db.py에서 약물 정보를 추출하여 SQLite DB에 로드
"""

import sqlite3
import json
import sys

# drug_info_complete_db 임포트
try:
    from drug_info_complete_db import DRUG_DATABASE
    print(f"[OK] DRUG_DATABASE 로드 완료: {len(DRUG_DATABASE)}개 약물")
except ImportError as e:
    print(f"[ERROR] 파일 임포트 실패: {e}")
    sys.exit(1)

def load_medications_to_db(db_path="pharma_mobile.db"):
    """약물 정보를 SQLite DB에 로드"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 테이블 재생성 (기존 데이터 유지)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            generic_name TEXT,
            dosage_strength TEXT,
            dosage_forms TEXT,
            daily_dose TEXT,
            frequency TEXT,
            duration TEXT,
            mfds_price TEXT,
            manufacturer TEXT,
            side_effects TEXT,
            contraindications TEXT,
            drug_interactions TEXT,
            special_warnings TEXT,
            indication TEXT,
            category TEXT,
            efficacy TEXT,
            clinical_trial TEXT,
            monitoring TEXT,
            price_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 데이터 준비
        medications_to_insert = []
        for drug_name, drug_info in DRUG_DATABASE.items():
            try:
                # 기본 정보
                generic_name = drug_info.get('generic_name', '')
                category = drug_info.get('category', '')
                indication = ', '.join(drug_info.get('indication', []))
                efficacy = drug_info.get('efficacy', '')
                clinical_trial = drug_info.get('clinical_trial', '')

                # 용량 정보
                dosage_info = drug_info.get('dosage', {})
                single_dose = dosage_info.get('single_dose', '')
                frequency = dosage_info.get('frequency', '')
                dosage_form = dosage_info.get('form', '')

                # 부작용
                side_effects_dict = drug_info.get('side_effects', {})
                side_effects_list = [f"{k}: {v}" for k, v in side_effects_dict.items()]
                side_effects_json = json.dumps(side_effects_list, ensure_ascii=False)

                # 상호작용
                interactions = drug_info.get('interactions', [])
                interactions_list = [f"{i['drug']}: {i['description']}" for i in interactions]
                interactions_json = json.dumps(interactions_list, ensure_ascii=False)

                # 경고
                warnings = drug_info.get('warnings', [])
                warnings_json = json.dumps(warnings, ensure_ascii=False)

                # 모니터링
                monitoring = drug_info.get('monitoring', {})
                monitoring_json = json.dumps(monitoring, ensure_ascii=False)

                # 가격
                price_info = drug_info.get('price', {})
                price_json = json.dumps(price_info, ensure_ascii=False)

                # DB에 삽입할 데이터
                medications_to_insert.append((
                    drug_name,                           # name
                    generic_name,                        # generic_name
                    single_dose,                         # dosage_strength
                    dosage_form,                         # dosage_forms
                    single_dose,                         # daily_dose
                    frequency,                           # frequency
                    "의사 지시에 따름",                  # duration
                    "",                                  # mfds_price (나중 추가)
                    "",                                  # manufacturer
                    side_effects_json,                   # side_effects
                    "",                                  # contraindications
                    interactions_json,                   # drug_interactions
                    warnings_json,                       # special_warnings
                    indication,                          # indication
                    category,                            # category
                    efficacy,                            # efficacy
                    clinical_trial,                      # clinical_trial
                    monitoring_json,                     # monitoring
                    price_json                           # price_info
                ))
            except Exception as e:
                print(f"[WARN] {drug_name} 처리 중 오류: {e}")
                continue

        # 배치 삽입
        cursor.executemany('''
        INSERT OR REPLACE INTO medications
        (name, generic_name, dosage_strength, dosage_forms, daily_dose,
         frequency, duration, mfds_price, manufacturer, side_effects,
         contraindications, drug_interactions, special_warnings, indication,
         category, efficacy, clinical_trial, monitoring, price_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', medications_to_insert)

        conn.commit()

        # 결과 확인
        cursor.execute('SELECT COUNT(*) FROM medications')
        total_count = cursor.fetchone()[0]

        conn.close()

        print(f"[OK] 약물 DB 로드 완료")
        print(f"     총 {total_count}개 약물 저장됨")
        print(f"     신규 추가: {len(medications_to_insert)}개")

        return True

    except Exception as e:
        print(f"[ERROR] DB 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = load_medications_to_db()
    sys.exit(0 if success else 1)
