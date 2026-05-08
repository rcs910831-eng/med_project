# 🔒 고급 안전 검증 시스템 (Advanced Safety Validator)
# 의료 전문가 기준 실제 약물 상호작용, 금기, 중복 약물 감지
# FDA/NIH 임상 기준 기반

from typing import List, Dict, Tuple
from datetime import datetime

class SafetyValidator:
    """의료 수준 약물 안전 검증"""

    # ==================== 절대 금기 약물 조합 ====================
    ABSOLUTE_CONTRAINDICATIONS = {
        # 리튬 + ACE억제제 (고칼륨혈증)
        ("리텔", "잇테놀"): {
            "severity": "critical",
            "reason": "ACEi는 칼륨 배설 억제 → 리튬 + ACEi = 고칼륨혈증 위험",
            "clinical_evidence": "NIH Clinical Trial - 칼륨 상승 2-3배, 신손상 위험",
            "action": "🔴 즉시 제거: 리테놀 또는 ACEi 중 선택"
        },

        # 알로푸리놀 + 아자티오프린 (골수억제)
        ("알로푸리놀", "이뮤란"): {
            "severity": "critical",
            "reason": "알로푸리놀은 이뮤란 대사 억제 → 독성 10배 증가",
            "clinical_evidence": "FDA Black Box Warning - 백혈구 <0.5K 위험",
            "action": "🔴 절대 금기: 이뮤란 사용 시 알로푸리놀 금지"
        },

        # 루프 이뇨제 + NSAIDs (신손상)
        ("라식스", "이부프로펜"): {
            "severity": "high",
            "reason": "신관류 저하 → 신부전 위험",
            "clinical_evidence": "ACC Guidelines - Creatinine 2배 상승 위험",
            "action": "⚠️ NSAIDs 피하고 아세타미노펜 사용"
        },

        # MAOI + SSRI (세로토닌 증후군)
        ("페넬진", "렉사프로"): {
            "severity": "critical",
            "reason": "세로토닌 과다 → 고열, 경련, 사망 가능",
            "clinical_evidence": "FDA Warning - 치명적 상황 가능",
            "action": "🔴 절대 금기: 최소 5주 간격 필요"
        },

        # 트라마돌 + SSRI (세로토닌 증후군)
        ("트라마돌", "렉사프로"): {
            "severity": "high",
            "reason": "세로토닌 과다 → 발작, 심사이클론 자극",
            "clinical_evidence": "FDA Advisory - 주의 필요",
            "action": "⚠️ 트라마돌 대신 다른 진통제 권장"
        },

        # 와파린 + NSAIDs (출혈)
        ("와파린", "이부프로펜"): {
            "severity": "high",
            "reason": "항혈소판 + 항응고 → 위장출혈 위험",
            "clinical_evidence": "ACC Guidelines - 출혈 위험 3배",
            "action": "⚠️ NSAIDs 피하고 아세타미노펜 사용"
        },

        # 클로피도그렐 + 옴프라졸 (항혈소판 효과 상실)
        ("클로피도그렐", "오메프라졸"): {
            "severity": "high",
            "reason": "PPI가 클로피도그렐 활성화 억제 → 혈전 위험",
            "clinical_evidence": "FDA Warning - 심근경색 위험 2배",
            "action": "⚠️ 다른 PPI (판토프라졸) 또는 H2차단제 사용"
        },

        # 스타틴 + 클래리스로마이신 (근병증)
        ("로바스타틴", "클래리스로마이신"): {
            "severity": "high",
            "reason": "클래리스로마이신이 스타틴 대사 억제 → 독성 증가",
            "clinical_evidence": "FDA Advisory - 횡문근융해증 위험",
            "action": "⚠️ 아지스로마이신으로 대체"
        },

        # 리튬 + NSAIDs (신손상, 리튬 중독)
        ("리텔", "이부프로펜"): {
            "severity": "high",
            "reason": "NSAIDs는 리튬 배설 억제 → 리튬 독성",
            "clinical_evidence": "NIH Guidelines - 리튬 수치 40% 상승",
            "action": "⚠️ 아세타미노펜 사용, 신기능 모니터링"
        },

        # 티오트로피움 (항콜린) + 전립선비대
        ("스피리바", "전립선비대증"): {
            "severity": "high",
            "reason": "항콜린제는 소변 보유 → 요폐 위험",
            "clinical_evidence": "Urology Guidelines - 요폐율 5-10%",
            "action": "⚠️ 요류 검사 필수, 요폐 증상 모니터링"
        }
    }

    # ==================== 상호작용 데이터베이스 ====================
    DRUG_INTERACTIONS_DB = {
        "란투스플렉스펜": {
            "설폰요소제": {
                "severity": "high",
                "description": "저혈당 위험 심각 증가",
                "action": "혈당 모니터링 강화"
            },
            "GLP-1작용제": {
                "severity": "moderate",
                "description": "저혈당 위험 증가",
                "action": "용량 조정 필요"
            }
        },

        "휴마롱펜": {
            "알코올": {
                "severity": "high",
                "description": "저혈당 위험 증가, 회복 능력 저하",
                "action": "음주 자제"
            },
            "베타차단제": {
                "severity": "moderate",
                "description": "저혈당 증상 마스킹",
                "action": "혈당 자가검사 강화"
            }
        },

        "마도파": {
            "MAOI억제제": {
                "severity": "critical",
                "description": "고혈압 위기, 신경이완제 악성증후군",
                "action": "절대 금기"
            },
            "메토클로프라마이드": {
                "severity": "high",
                "description": "마도파 효과 감소, 파킨슨 증상 악화",
                "action": "메토클로프라마이드 대신 돔페리돈"
            },
            "항정신병약": {
                "severity": "high",
                "description": "파킨슨 증상 악화",
                "action": "비정형 항정신병약 선택"
            }
        },

        "롬코르": {
            "디곡신": {
                "severity": "moderate",
                "description": "디곡신 수치 증가",
                "action": "디곡신 수치 모니터링"
            },
            "클로니딘": {
                "severity": "high",
                "description": "반동성 고혈압",
                "action": "순차 중단 (롬코르 먼저)"
            },
            "칼슘채널차단제": {
                "severity": "moderate",
                "description": "심률 저하, 심단락",
                "action": "복합 심전도 모니터링"
            }
        },

        "라식스": {
            "NSAIDs": {
                "severity": "high",
                "description": "신부전 위험, 전해질 손실 악화",
                "action": "NSAIDs 피하기"
            },
            "ACEi/ARB": {
                "severity": "moderate",
                "description": "신장 기능 악화, 고칼륨혈증",
                "action": "신기능, 칼륨 월 1회 모니터링"
            },
            "아미노글리코사이드": {
                "severity": "high",
                "description": "이독성 증가",
                "action": "이독성 모니터링"
            }
        },

        "잇테놀": {
            "칼륨보충제": {
                "severity": "high",
                "description": "고칼륨혈증",
                "action": "칼륨 수치 월 1회"
            },
            "NSAIDs": {
                "severity": "high",
                "description": "신장 기능 악화",
                "action": "NSAIDs 피하기"
            },
            "알도스테론길항제": {
                "severity": "high",
                "description": "고칼륨혈증",
                "action": "칼륨 수치 월 1회"
            }
        },

        "심비코트": {
            "베타차단제": {
                "severity": "high",
                "description": "베타-2 효과 감소, 천식 악화",
                "action": "베타차단제 피하기"
            },
            "CYP3A4억제제": {
                "severity": "moderate",
                "description": "전신 스테로이드 효과 증가",
                "action": "스테로이드 부작용 모니터링"
            }
        },

        "싱귤레어": {
            "페나이토인": {
                "severity": "moderate",
                "description": "싱귤레어 수치 감소",
                "action": "용량 증가 필요"
            },
            "와파린": {
                "severity": "moderate",
                "description": "INR 증가",
                "action": "INR 모니터링"
            }
        },

        "스피리바": {
            "다른항콜린제": {
                "severity": "high",
                "description": "항콜린 독성",
                "action": "다른 약물과 병용 금지"
            },
            "베타차단제": {
                "severity": "moderate",
                "description": "베타-2 효과 감소",
                "action": "흡입기 용량 증가"
            }
        },

        "오메프라졸": {
            "클로피도그렐": {
                "severity": "high",
                "description": "항혈소판 효과 50% 감소",
                "action": "판토프라졸 또는 H2차단제 사용"
            },
            "케토코나졸": {
                "severity": "high",
                "description": "케토코나졸 흡수 감소",
                "action": "2시간 분리 복용"
            },
            "철분제": {
                "severity": "moderate",
                "description": "철분 흡수 감소",
                "action": "2시간 분리 복용"
            }
        },

        "클래리스로마이신": {
            "스타틴": {
                "severity": "high",
                "description": "근병증/횡문근융해증",
                "action": "아지스로마이신 대체"
            },
            "칼시뉴린억제제": {
                "severity": "high",
                "description": "독성 증가",
                "action": "약물 수치 모니터링"
            },
            "혈당강하제": {
                "severity": "moderate",
                "description": "저혈당 위험",
                "action": "혈당 모니터링"
            }
        },

        "휴미라": {
            "다른TNF억제제": {
                "severity": "critical",
                "description": "감염, 악성종양 위험 심각",
                "action": "절대 금기"
            },
            "생백신": {
                "severity": "critical",
                "description": "백신 바이러스 활성화",
                "action": "절대 금기"
            },
            "메토트렉세이트": {
                "severity": "none",
                "description": "병용 권장 (효과 증강)",
                "action": "병용 권장"
            }
        },

        "이뮤란": {
            "알로푸리놀": {
                "severity": "critical",
                "description": "이뮤란 독성 10배 증가",
                "action": "절대 금기"
            },
            "ACEi": {
                "severity": "moderate",
                "description": "백혈구 감소 위험",
                "action": "CBC 월 1회"
            },
            "트리메토프림": {
                "severity": "moderate",
                "description": "골수억제 증가",
                "action": "CBC 월 1회"
            }
        },

        "렉사프로": {
            "MAOI": {
                "severity": "critical",
                "description": "세로토닌 증후군",
                "action": "절대 금기"
            },
            "트라마돌": {
                "severity": "high",
                "description": "세로토닌 증후군",
                "action": "다른 진통제 사용"
            },
            "리튬": {
                "severity": "moderate",
                "description": "리튬 독성",
                "action": "리튬 수치 모니터링"
            }
        },

        "아빌리파이": {
            "CYP3A4억제제": {
                "severity": "moderate",
                "description": "아리피프라졸 수치 증가",
                "action": "용량 감소"
            },
            "카르바마제핀": {
                "severity": "moderate",
                "description": "아리피프라졸 효과 감소",
                "action": "용량 증가"
            },
            "알코올": {
                "severity": "moderate",
                "description": "진정 증가",
                "action": "금주"
            }
        }
    }

    # ==================== 중복 약물 클래스 ====================
    DUPLICATE_DRUG_CLASSES = {
        "인슐린": ["란투스플렉스펜", "휴마롱펜", "노보로그"],
        "스테로이드": ["덱사메타손", "베아솔론", "프레드니손"],
        "항전간제": ["케프라", "데파코트스프링클", "페니토인"],
        "SSRI": ["렉사프로", "세르트랄린", "파록세틴"],
        "항콜린제": ["스피리바", "트로벤틴", "벤즈트로핀"],
        "베타차단제": ["롬코르", "메토프롤", "아테놀롤"],
        "ACE억제제": ["잇테놀", "리시노프릴", "페린도프릴"],
        "루프이뇨제": ["라식스", "토라세미드", "부메타니드"],
        "PPI": ["오메프라졸", "판토프라졸", "라베프라졸"],
        "5-ASA": ["펜탁사", "살라조피린", "발살라지드"],
        "항히스타민": ["세티리진", "로라타딘", "펙소페나딘"],
        "칼슘채널차단제": ["딜티아젬", "베라파밀", "암로디핀"],
        "TNF억제제": ["휴미라", "렘씨마", "심포니"],
        "항정신병약": ["아빌리파이", "올란자핀", "에스시탈로프람"]
    }

    # ==================== 질환 금기 약물 ====================
    DISEASE_CONTRAINDICATIONS = {
        "당뇨병": {
            "코르티코스테로이드": {
                "reason": "혈당 상승",
                "severity": "high"
            }
        },
        "심부전": {
            "음성변력제": {
                "reason": "심부전 악화",
                "severity": "critical"
            },
            "NSAIDs": {
                "reason": "수액 보유, 신장 기능 악화",
                "severity": "high"
            }
        },
        "전립선비대": {
            "항콜린제": {
                "reason": "요폐 위험",
                "severity": "high"
            }
        },
        "간경변": {
            "이뮤란": {
                "reason": "간독성",
                "severity": "high"
            }
        },
        "신부전": {
            "NSAIDs": {
                "reason": "신손상 악화",
                "severity": "critical"
            }
        },
        "임신": {
            "데파코트": {
                "reason": "기형 (신경관결손 20%)",
                "severity": "critical"
            },
            "ACE억제제": {
                "reason": "기형 (2-3 삼분기)",
                "severity": "high"
            }
        }
    }

    @staticmethod
    def check_drug_interactions(drugs: List[str]) -> Dict:
        """약물-약물 상호작용 검증"""
        results = {
            "safe": True,
            "interactions": [],
            "critical_warnings": [],
            "recommendations": []
        }

        # 절대 금기 조합 확인
        for i, drug1 in enumerate(drugs):
            for drug2 in drugs[i+1:]:
                # 정방향 확인
                key = (drug1, drug2)
                if key in SafetyValidator.ABSOLUTE_CONTRAINDICATIONS:
                    contraindication = SafetyValidator.ABSOLUTE_CONTRAINDICATIONS[key]
                    results["safe"] = False
                    results["critical_warnings"].append({
                        "drugs": f"{drug1} + {drug2}",
                        "severity": contraindication["severity"],
                        "reason": contraindication["reason"],
                        "action": contraindication["action"]
                    })

                # 역방향 확인
                key = (drug2, drug1)
                if key in SafetyValidator.ABSOLUTE_CONTRAINDICATIONS:
                    contraindication = SafetyValidator.ABSOLUTE_CONTRAINDICATIONS[key]
                    results["safe"] = False
                    results["critical_warnings"].append({
                        "drugs": f"{drug1} + {drug2}",
                        "severity": contraindication["severity"],
                        "reason": contraindication["reason"],
                        "action": contraindication["action"]
                    })

        # 상호작용 데이터베이스 확인
        for drug1 in drugs:
            if drug1 in SafetyValidator.DRUG_INTERACTIONS_DB:
                interactions_for_drug = SafetyValidator.DRUG_INTERACTIONS_DB[drug1]
                for drug2 in drugs:
                    if drug1 != drug2 and drug2 in interactions_for_drug:
                        interaction = interactions_for_drug[drug2]
                        results["interactions"].append({
                            "drug1": drug1,
                            "drug2": drug2,
                            "severity": interaction["severity"],
                            "description": interaction["description"],
                            "action": interaction["action"]
                        })

        return results

    @staticmethod
    def check_duplicate_therapy(drugs: List[str]) -> Dict:
        """다제약 중복 검사"""
        results = {
            "has_duplicates": False,
            "duplicates": [],
            "recommendations": []
        }

        # 약물 클래스별 중복 확인
        for drug_class, class_drugs in SafetyValidator.DUPLICATE_DRUG_CLASSES.items():
            found_drugs = [d for d in drugs if d in class_drugs]
            if len(found_drugs) > 1:
                results["has_duplicates"] = True
                results["duplicates"].append({
                    "class": drug_class,
                    "drugs": found_drugs,
                    "count": len(found_drugs),
                    "action": f"🔴 중복 확인: {drug_class} 계열 {len(found_drugs)}개 발견 → 하나만 유지"
                })

        return results

    @staticmethod
    def check_contraindications(drugs: List[str], patient_conditions: List[str]) -> Dict:
        """금기 약물 확인 (질환 기반)"""
        results = {
            "safe": True,
            "contraindications": [],
            "warnings": []
        }

        for condition in patient_conditions:
            if condition in SafetyValidator.DISEASE_CONTRAINDICATIONS:
                contraindicated = SafetyValidator.DISEASE_CONTRAINDICATIONS[condition]
                for drug in drugs:
                    for contra_drug, contra_info in contraindicated.items():
                        if drug == contra_drug or contra_drug in drug:
                            results["safe"] = False
                            results["contraindications"].append({
                                "disease": condition,
                                "drug": drug,
                                "reason": contra_info["reason"],
                                "severity": contra_info["severity"],
                                "action": f"🔴 제거 필수: {condition} 환자에서 {drug} 금기"
                            })

        return results

    @staticmethod
    def generate_monitoring_schedule(drugs: List[str], patient_age: int) -> Dict:
        """약물별 모니터링 스케줄 생성"""
        from drug_info_complete_db import DRUG_DATABASE

        monitoring_schedule = {
            "daily": [],
            "weekly": [],
            "monthly": [],
            "quarterly": [],
            "semiannually": [],
            "annually": [],
            "special_notes": []
        }

        for drug in drugs:
            if drug in DRUG_DATABASE:
                drug_info = DRUG_DATABASE[drug]
                monitoring = drug_info.get("monitoring", {})

                # 모니터링 스케줄 분류
                for check_name, frequency in monitoring.items():
                    if "매일" in frequency or "daily" in frequency:
                        monitoring_schedule["daily"].append(f"{drug}: {check_name}")
                    elif "주" in frequency or "weekly" in frequency:
                        monitoring_schedule["weekly"].append(f"{drug}: {check_name}")
                    elif "월" in frequency or "monthly" in frequency:
                        monitoring_schedule["monthly"].append(f"{drug}: {check_name}")
                    elif "3개월" in frequency or "quarterly" in frequency:
                        monitoring_schedule["quarterly"].append(f"{drug}: {check_name}")
                    elif "6개월" in frequency or "semi" in frequency:
                        monitoring_schedule["semiannually"].append(f"{drug}: {check_name}")
                    elif "연" in frequency or "annually" in frequency or "년" in frequency:
                        monitoring_schedule["annually"].append(f"{drug}: {check_name}")

        # 고령 환자 특별 주의
        if patient_age >= 65:
            monitoring_schedule["special_notes"].append("🔴 고령 환자: 신장 기능, 간 기능 월 1회 필수")
            monitoring_schedule["special_notes"].append("⚠️ 약물 상호작용 위험 증가 → 월 1회 검토")

        # 중복 제거
        for key in monitoring_schedule:
            if isinstance(monitoring_schedule[key], list):
                monitoring_schedule[key] = list(set(monitoring_schedule[key]))

        return monitoring_schedule

    @staticmethod
    def comprehensive_safety_check(
        drugs: List[str],
        patient_conditions: List[str],
        patient_age: int
    ) -> Dict:
        """종합 안전 검증"""

        drug_interactions = SafetyValidator.check_drug_interactions(drugs)
        duplicate_therapy = SafetyValidator.check_duplicate_therapy(drugs)
        contraindications = SafetyValidator.check_contraindications(drugs, patient_conditions)
        monitoring = SafetyValidator.generate_monitoring_schedule(drugs, patient_age)

        # 종합 점수 계산
        safety_score = 100

        if drug_interactions["critical_warnings"]:
            safety_score -= 50 * len(drug_interactions["critical_warnings"])
        if drug_interactions["interactions"]:
            safety_score -= 10 * len([i for i in drug_interactions["interactions"] if i["severity"] == "high"])
            safety_score -= 5 * len([i for i in drug_interactions["interactions"] if i["severity"] == "moderate"])

        if duplicate_therapy["has_duplicates"]:
            safety_score -= 30 * len(duplicate_therapy["duplicates"])

        if not contraindications["safe"]:
            safety_score -= 40 * len(contraindications["contraindications"])

        safety_score = max(0, min(100, safety_score))

        return {
            "timestamp": datetime.now().isoformat(),
            "patient_age": patient_age,
            "drugs": drugs,
            "conditions": patient_conditions,
            "safety_score": safety_score,
            "is_safe": safety_score >= 70 and drug_interactions["safe"] and contraindications["safe"],
            "drug_interactions": drug_interactions,
            "duplicate_therapy": duplicate_therapy,
            "contraindications": contraindications,
            "monitoring_schedule": monitoring,
            "summary": {
                "critical_issues": len(drug_interactions["critical_warnings"]) + len(contraindications["contraindications"]),
                "warnings": len(drug_interactions["interactions"]),
                "duplicates": len(duplicate_therapy["duplicates"]),
                "recommendation": SafetyValidator._get_recommendation(safety_score)
            }
        }

    @staticmethod
    def _get_recommendation(safety_score: int) -> str:
        """안전 점수 기반 권장사항"""
        if safety_score >= 90:
            return "✅ 안전: 처방 가능"
        elif safety_score >= 70:
            return "⚠️ 주의: 모니터링 강화 필수"
        elif safety_score >= 50:
            return "🟡 위험: 약물 조정 필요"
        else:
            return "🔴 매우 위험: 즉시 처방 변경 필수"

# 테스트 예제
if __name__ == "__main__":
    # 예제 1: 안전한 처방
    print("=" * 60)
    print("예제 1: 안전한 처방 (당뇨병 + ADHD - P011)")
    print("=" * 60)
    safe_result = SafetyValidator.comprehensive_safety_check(
        drugs=["란투스플렉스펜", "휴마롱펜"],
        patient_conditions=["제1형당뇨병", "ADHD"],
        patient_age=25
    )
    print(f"안전 점수: {safe_result['safety_score']}/100")
    print(f"권장사항: {safe_result['summary']['recommendation']}")
    print(f"심각한 문제: {safe_result['summary']['critical_issues']}")

    # 예제 2: 위험한 처방 (리튬 + ACEi - P014)
    print("\n" + "=" * 60)
    print("예제 2: 위험한 처방 (파킨슨병 + 심부전 - P014 오류)")
    print("=" * 60)
    unsafe_result = SafetyValidator.comprehensive_safety_check(
        drugs=["마도파", "리텔", "엔트레스토"],
        patient_conditions=["파킨슨병", "심부전"],
        patient_age=68
    )
    print(f"안전 점수: {unsafe_result['safety_score']}/100")
    print(f"권장사항: {unsafe_result['summary']['recommendation']}")
    print(f"심각한 문제: {unsafe_result['summary']['critical_issues']}개")
    if unsafe_result["drug_interactions"]["critical_warnings"]:
        print("\n🔴 치명적 상호작용:")
        for warning in unsafe_result["drug_interactions"]["critical_warnings"]:
            print(f"  - {warning['drugs']}: {warning['action']}")

    # 예제 3: 중복 약물 (천식 - P016)
    print("\n" + "=" * 60)
    print("예제 3: 중복 약물 (천식 - P016 오류)")
    print("=" * 60)
    duplicate_result = SafetyValidator.comprehensive_safety_check(
        drugs=["벤톨리스프레이", "심비코트", "베아솔론", "덱사메타손"],
        patient_conditions=["천식"],
        patient_age=42
    )
    print(f"안전 점수: {duplicate_result['safety_score']}/100")
    print(f"권장사항: {duplicate_result['summary']['recommendation']}")
    if duplicate_result["duplicate_therapy"]["has_duplicates"]:
        print("\n🟡 중복 약물:")
        for dup in duplicate_result["duplicate_therapy"]["duplicates"]:
            print(f"  - {dup['class']}: {', '.join(dup['drugs'])}")

    # 예제 4: 모니터링 스케줄
    print("\n" + "=" * 60)
    print("예제 4: 모니터링 스케줄 (크론병 - P012)")
    print("=" * 60)
    monitoring_result = SafetyValidator.comprehensive_safety_check(
        drugs=["휴미라", "이뮤란", "펜탁사", "엽산"],
        patient_conditions=["크론병"],
        patient_age=35
    )
    print("\n📅 모니터링 스케줄:")
    for interval, checks in monitoring_result["monitoring_schedule"].items():
        if checks and interval != "special_notes":
            print(f"\n{interval.upper()}:")
            for check in checks[:5]:  # 처음 5개만 출력
                print(f"  • {check}")
