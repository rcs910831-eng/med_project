#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHIELD PHARMA-HYBRID v21.0 - Main Managed Agents Entry Point
Integrated multi-agent medical prescription analysis system
"""

import os
import json
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

from agents.agent_orchestrator import AgentOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pharma_hybrid_v21.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PHARMA-HYBRID")

def main():
    # Load environment variables explicitly
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    
    parser = argparse.ArgumentParser(description="SHIELD PHARMA-HYBRID v21.0 - Prescription Analysis")
    parser.add_argument("--image", type=str, help="Path to prescription image", default="prescription_images/RX_P001.png")
    parser.add_argument("--lat", type=float, help="Patient latitude", default=37.5665)
    parser.add_argument("--lon", type=float, help="Patient longitude", default=126.9780)
    parser.add_argument("--address", type=str, help="Patient address", default="서울특별시 중구 세종대로 110")
    parser.add_argument("--output", type=str, help="Output directory", default="./pharma_output")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    print("\n" + "="*60)
    print("      SHIELD PHARMA-HYBRID v21.0 - STRATEGIC COMMAND")
    print("="*60)
    
    # Initialize Orchestrator
    try:
        orchestrator = AgentOrchestrator()
        logger.info("Orchestrator system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        return

    # Process Prescription
    image_path = args.image
    if not os.path.exists(image_path):
        logger.error(f"Prescription image not found: {image_path}")
        return

    patient_location = {
        "latitude": args.lat,
        "longitude": args.lon,
        "address": args.address
    }

    print(f"\n[SYSTEM] Starting analysis for: {image_path}")
    print(f"[SYSTEM] Location: {args.address} ({args.lat}, {args.lon})")
    
    report_data = orchestrator.process_prescription_image(
        image_path=image_path,
        patient_location=patient_location
    )

    if not report_data:
        print("\n[ERROR] Prescription analysis failed. Please check logs.")
        return

    # Generate Reports (PDF, HTML, Voice)
    print("\n[SYSTEM] Generating comprehensive reports...")
    report_files = orchestrator.generate_reports(report_data, output_dir=args.output)

    # Output Summary
    print("\n" + "-"*60)
    print("                ANALYSIS COMPLETE")
    print("-"*60)
    
    patient = report_data.get("patient", {})
    print(f"환자명: {patient.get('name')} ({patient.get('age')}세, {patient.get('sex')})")
    print(f"주진료: {patient.get('diagnosis_primary')}")
    print(f"처방약: {', '.join([m.get('name') for m in report_data.get('medications', [])])}")
    
    print("\n[생성된 파일]")
    for fmt, path in report_files.items():
        if path:
            print(f"- {fmt.upper()}: {path}")

    print("\n" + "="*60)
    print("      SHIELD PHARMA-HYBRID v21.0 - SYSTEM READY")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
