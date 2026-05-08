import os
import json
import shutil
from datetime import datetime

class DataPipeline:
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self.raw_text_dir = os.path.join(base_dir, "raw", "texts")
        self.raw_img_dir = os.path.join(base_dir, "raw", "images")
        self.raw_db_dir = os.path.join(base_dir, "raw", "dbs")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.metadata_file = os.path.join(self.processed_dir, "metadata.json")
        self.review_file = os.path.join(self.processed_dir, "review_status.json")
        
        self._initialize_directories()
        self._initialize_json_safely(self.metadata_file, [])
        self._initialize_json_safely(self.review_file, [])

    def _initialize_directories(self):
        """기본 폴더 구조를 생성합니다."""
        dirs = [self.raw_text_dir, self.raw_img_dir, self.raw_db_dir, self.processed_dir]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            print(f"[Init] 디렉토리 확인: {d}")

    def _initialize_json_safely(self, filepath, default_data):
        """JSON 파일이 없으면 기본 데이터로 생성합니다."""
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
            print(f"[Init] 메타데이터/리뷰 파일 생성: {filepath}")

    def ingest_file(self, source_path, file_type, category="uncategorized"):
        """새로운 파일을 파이프라인으로 가져오고 메타데이터를 기록합니다."""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"원본 파일을 찾을 수 없습니다: {source_path}")

        filename = os.path.basename(source_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_name = f"{timestamp}_{filename}"

        if file_type == "text":
            target_path = os.path.join(self.raw_text_dir, target_name)
        elif file_type == "image":
            target_path = os.path.join(self.raw_img_dir, target_name)
        elif file_type == "db":
            target_path = os.path.join(self.raw_db_dir, target_name)
        else:
            raise ValueError("file_type은 'text', 'image', 'db' 중 하나여야 합니다.")

        shutil.copy2(source_path, target_path)
        
        # 메타데이터 기록
        metadata_entry = {
            "id": target_name,
            "original_filename": filename,
            "file_type": file_type,
            "category": category, # e.g., 'diet', 'drug_interaction', 'pill_image'
            "ingested_at": datetime.now().isoformat(),
            "path": target_path,
            "status": "pending_processing"
        }

        self._append_metadata(metadata_entry)
        print(f"[Ingest] 성공: {filename} -> {target_path}")
        return target_path

    def _append_metadata(self, new_entry):
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []

        data.append(new_entry)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    print("=== 약사 AI 데이터 파이프라인 초기화 ===")
    pipeline = DataPipeline()
    print("초기화 완료되었습니다.")
