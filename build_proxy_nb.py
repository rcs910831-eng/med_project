import json
import os

def build_proxy_integrated_nb():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# PHARMA-HYBRID OS (Ver 1.5): 대리인/보호자 통합 모드\n",
                    "### [수석 아키텍트 조언: 보호자의 관찰 데이터가 환자의 생명을 구합니다]\n",
                    "\n",
                    "이 버전은 대리인(보호자)이 환자를 대신해 정보를 제공하고 가이드를 받을 수 있는 기능을 탑재했습니다.\n",
                    "\n",
                    "---"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 필수 라이브러리 설치\n",
                    "!pip install -q pillow pandas numpy pyyaml nest-asyncio"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. 데이터 아키텍처: 대리인 컨텍스트 정의"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import os, json, asyncio, yaml\n",
                    "\n",
                    "class ProxyContextManager:\n",
                    "    \"\"\"대리인 정보를 관리하는 모듈\"\"\"\n",
                    "    def __init__(self, relationship=\"보호자\", observation=\"\"):\n",
                    "        self.relationship = relationship\n",
                    "        self.observation = observation\n",
                    "        \n",
                    "    def get_proxy_header(self):\n",
                    "        return f\"[대리인 모드 가동: {self.relationship}]\"\n",
                    "\n",
                    "class DataArchitect:\n",
                    "    def __init__(self, kb_path=\"knowledge_base.json\"):\n",
                    "        self.kb_path = kb_path\n",
                    "        \n",
                    "    def load_drug_data(self):\n",
                    "        with open(self.kb_path, \"r\", encoding=\"utf-8\") as f:\n",
                    "            return json.load(f).get(\"drugs\", [])\n",
                    "\n",
                    "architect = DataArchitect()\n",
                    "drugs = architect.load_drug_data()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. 하이브리드 엔진 & 메디컬 브레인"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "class MedicalBrain:\n",
                    "    def process_with_proxy(self, trinity_data, proxy_context, drugs):\n",
                    "        print(f\"\\n{proxy_context.get_proxy_header()} 데이터 분석 중...\")\n",
                    "        # 대리인이 관찰한 증상(observation)과 약물 부작용 매칭 로직\n",
                    "        match = drugs[0] # 샘플 매칭\n",
                    "        return match"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. 보호자 맞춤형 전문가 리포트 (Ver 1.5 핵심)\n",
                    "환자 본인이 아닌 대리인에게 '행동 지침'을 명확히 전달합니다."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "class ExpertCaregiverReporter:\n",
                    "    def generate(self, drug_info, proxy_context):\n",
                    "        name = drug_info.get('name', '미확인')\n",
                    "        cat = drug_info.get('category', '정보 없음')\n",
                    "        \n",
                    "        rep = f\"\\n{'='*60}\\n\"\n",
                    "        rep += f\"      [30년 경력 약사 AI: 보호자님께 드리는 복약 가이드]\\n\"\n",
                    "        rep += f\"{'='*60}\\n\"\n",
                    "        rep += f\"■ 환자 관계: {proxy_context.relationship}\\n\"\n",
                    "        rep += f\"■ 판독 제품: {name}\\n\\n\"\n",
                    "        \n",
                    "        rep += f\"■ 보호자님을 위한 행동 지침:\\n\"\n",
                    "        rep += f\"1. 환자분께 이 약({name})을 드릴 때, {drug_info.get('precautions', '전문가 조언을 따르세요.')}\\n\"\n",
                    "        \n",
                    "        if \"암\" in cat:\n",
                    "            rep += \"\\n[항암 관리 포인트]\\n\"\n",
                    "            rep += \"- 환자분이 약을 삼키기 어려워하시는지(연하곤란) 관찰해 주세요.\\n\"\n",
                    "            rep += \"- 대리인께서 관찰하신 '{proxy_context.observation}' 증상이 심해지면 즉시 병원에 연락하십시오.\\n\"\n",
                    "            \n",
                    "        if \"어린이\" in name or \"시럽\" in name:\n",
                    "            rep += \"\\n[어린이 투약 포인트]\\n\"\n",
                    "            rep += \"- 아이가 약을 뱉지 않도록 소량씩 천천히 복용시켜 주세요.\\n\"\n",
                    "            \n",
                    "        rep += f\"\\n{'='*60}\"\n",
                    "        return rep"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 4. 시스템 가동 (대리인 모드 시뮬레이션)"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import nest_asyncio\n",
                    "nest_asyncio.apply()\n",
                    "\n",
                    "async def run_proxy_mode():\n",
                    "    # 상황: 아들이 암 투병 중인 어머니의 약을 대신 분석\n",
                    "    proxy = ProxyContextManager(relationship=\"아들\", observation=\"손발이 조금 붓고 계심\")\n",
                    "    \n",
                    "    brain = MedicalBrain()\n",
                    "    reporter = ExpertCaregiverReporter()\n",
                    "    \n",
                    "    # 분석 및 리포트\n",
                    "    final_data = brain.process_with_proxy({}, proxy, drugs)\n",
                    "    print(reporter.generate(final_data, proxy))\n",
                    "\n",
                    "await run_proxy_mode()"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": { "name": "python", "version": "3.11.0" }
        },
        "nbformat": 4, "nbformat_minor": 4\n",
    }\n",
    "    with open(\"AI_Pharmacist_System.ipynb\", \"w\", encoding=\"utf-8\") as f:\n",
    "        json.dump(nb, f, ensure_ascii=False, indent=1)\n",
    "    print(\"AI_Pharmacist_System.ipynb (Ver 1.5 - Proxy Mode) 빌드 완료!\")\n",
    "\n",
    "if __name__ == \"__main__\":\n",
    "    build_proxy_integrated_nb()\n"
