import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_core.prompts import PromptTemplate
import argparse

# 모델 설정은 유연하게 변경 가능하도록 팩토리/파라미터화
# 필요한 패키지가 설치되어 있어야 합니다 (예: langchain, langchain-google-genai, langchain-anthropic 등)
def get_llm(model_name="gemini"):
    if model_name.lower() == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        # GOOGLE_API_KEY 환경변수 필요
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
    elif model_name.lower() == "claude":
        from langchain_anthropic import ChatAnthropic
        # ANTHROPIC_API_KEY 환경변수 필요
        return ChatAnthropic(model_name="claude-3-haiku-20240307", temperature=0.1)
    elif model_name.lower() == "openai":
        from langchain_openai import ChatOpenAI
        # OPENAI_API_KEY 환경변수 필요
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    else:
        raise ValueError(f"지원하지 않는 LLM 모델입니다: {model_name}")

class RAGProcessor:
    def __init__(self, llm_type="gemini"):
        self.llm = get_llm(llm_type)
        self.kb_path = "knowledge_base.json"
        
        # 질환별 맞춤 식단 및 약물 상호작용 추출 프롬프트
        self.extraction_prompt = PromptTemplate.from_template(
            """
            당신은 30년 경력의 전문 임상 약사이자 영양사입니다. 
            아래에 제공된 문서 텍스트에서 '질환별 맞춤 식단'에 대한 정보와 '약물 상호작용'에 대한 정보를 추출하여 JSON 형태로 엄격하게 반환하세요.
            해당 정보가 없다면 null 또는 빈 배열을 반환하세요.

            문서 내용:
            {text}

            출력 제약 조건:
            반드시 아래의 JSON 스키마를 따르는 순수 JSON 문자열만 응답하세요. (마크다운 ```json 등은 제외)
            
            {{
                "extracted_diets": [
                    {{
                        "hospital_name": "알 수 없음 (문서 내 언급있으면 기재)",
                        "disease_type": "질환명 (예: kidney, liver, diabetes)",
                        "guide": "식단 가이드 요약"
                    }}
                ],
                "extracted_interactions": [
                    {{
                        "drug_name": "약물명",
                        "interaction_target": "상호작용 대상 (예: alcohol, supplements, specific_drug)",
                        "interaction_guide": "상호작용 상세 내용 및 지침"
                    }}
                ]
            }}
            """
        )

    def load_and_split_documents(self, source_dir="data/raw/texts"):
        if not os.path.exists(source_dir):
            print(f"[Warning] {source_dir} 디렉토리가 없습니다.")
            return []
            
        print(f"[RAG] 문서 로드 중... ({source_dir})")
        # PDF 대신 Text. txt, md 등 다양한 텍스트 파일 지원. (원한다면 glob "*.txt" 등으로 필터 가능)
        loader = DirectoryLoader(source_dir, glob="**/*.*", loader_cls=TextLoader, loader_kwargs={'autodetect_encoding': True})
        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)
        print(f"[RAG] 총 {len(chunks)}개의 청크(Chunk)로 분할되었습니다.")
        return chunks

    def process_and_extract(self, chunks):
        extracted_data_list = []
        chain = self.extraction_prompt | self.llm
        
        for i, chunk in enumerate(chunks):
            print(f"[RAG] 청크 {i+1}/{len(chunks)} 처리 중...")
            try:
                response = chain.invoke({"text": chunk.page_content})
                # 응답에서 마크다운 백틱 제거
                raw_json = response.content.replace("```json", "").replace("```", "").strip()
                data = json.loads(raw_json)
                extracted_data_list.append(data)
            except Exception as e:
                print(f"[Error] 청크 {i+1} 처리 실패: {e}")
                
        return extracted_data_list

    def update_knowledge_base(self, extracted_data_list):
        if not os.path.exists(self.kb_path):
            kb = {"hospitals": [], "drugs": [], "lifestyle_coaching": {}}
        else:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                kb = json.load(f)
                
        # 추출된 데이터를 KB 구조에 맞게 임시 편입 (검수 대시보드 연동을 위해 pending 상태 파일로 따로 저장할 수도 있음)
        review_buffer_path = "data/processed/pending_review.json"
        
        try:
            with open(review_buffer_path, 'r', encoding='utf-8') as f:
                pending_review = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pending_review = []

        for data in extracted_data_list:
            if data.get("extracted_diets") or data.get("extracted_interactions"):
                pending_review.append(data)

        # 바로 knowledge_base.json을 덮어쓰지 않고 대시보드 검수용으로 저장
        os.makedirs(os.path.dirname(review_buffer_path), exist_ok=True)
        with open(review_buffer_path, 'w', encoding='utf-8') as f:
            json.dump(pending_review, f, ensure_ascii=False, indent=4)
            
        print(f"[RAG] 처리 완료. 추출된 항목들을 {review_buffer_path}에 저장하여 검수 대기열에 올렸습니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Preprocessor for AI Pharmacist")
    parser.add_argument("--llm", type=str, default="gemini", help="LLM model (gemini, claude, openai)")
    args = parser.parse_args()
    
    print(f"=== RAG 기반 정보 추출 파이프라인 시작 (LLM: {args.llm}) ===")
    processor = RAGProcessor(llm_type=args.llm)
    chunks = processor.load_and_split_documents()
    if chunks:
        extracted = processor.process_and_extract(chunks)
        processor.update_knowledge_base(extracted)
    else:
        print("처리할 텍스트 문서가 없습니다.")
