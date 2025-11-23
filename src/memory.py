import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import STORY_CONTEXT_WINDOW

class LoreBook:
    def __init__(self):
        # 1. 임베딩 모델 준비 (텍스트 -> 숫자 변환기)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # 2. 벡터 저장소 (아직 데이터가 없으므로 None)
        self.vector_store = None
        
        # 3. [핵심] 책갈피 (어디까지 저장했는지 기억하는 커서)
        self.last_archived_index = 0

    def check_and_archive(self, story_parts: List[str]):
        """
        전체 이야기 리스트를 받아서, 윈도우 밖으로 밀려난 부분이 있으면 저장합니다.
        """
        total_length = len(story_parts)
        
        # 저장해야 할 한계선 (Boundary) 계산
        # 예: 전체 10개, 윈도우 5개 -> 인덱스 5까지는 저장해야 함 (0,1,2,3,4)
        boundary_index = total_length - STORY_CONTEXT_WINDOW
        
        # 저장할 게 없다면(아직 윈도우 안쪽이라면) 패스
        if boundary_index <= self.last_archived_index:
            return

        # --- 저장 로직 시작 ---
        print(f"\n📚 [LoreBook] 정리할 문단 발견! (인덱스 {self.last_archived_index} ~ {boundary_index})")
        
        # 1. 저장할 문단들만 쏙 뽑아내기 (Slicing)
        chunks_to_archive = story_parts[self.last_archived_index : boundary_index]
        
        # 2. 벡터 DB에 넣기
        self._add_documents(chunks_to_archive)
        
        # 3. [핵심] 책갈피 업데이트 (이제 여기까지 저장했다고 표시)
        self.last_archived_index = boundary_index
        print(f"✅ [LoreBook] 저장 완료. 현재 커서 위치: {self.last_archived_index}")

    def _add_documents(self, texts: List[str]):
        """실제로 FAISS DB에 데이터를 넣는 내부 함수"""
        if not texts:
            return
            
        # 텍스트를 Document 객체로 변환 (메타데이터 추가 가능)
        documents = [
            Document(page_content=text, metadata={"source": "story_archive"})
            for text in texts
        ]
        
        if self.vector_store is None:
            # DB가 없으면 새로 생성
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            # 있으면 추가
            self.vector_store.add_documents(documents)

    def search_relevant_info(self, query: str, k: int = 3) -> str:
        """
        현재 상황(query)과 관련된 과거 기억을 검색해서 텍스트로 반환합니다.
        """
        if self.vector_store is None:
            return "아직 기록된 과거 설정이 없습니다."
            
        # 유사도 검색 실행
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            # 검색된 내용들을 하나의 문자열로 합침
            result = "\n".join([f"- {doc.page_content}" for doc in docs])
            return result
        except Exception as e:
            print(f"⚠️ 검색 중 오류 발생: {e}")
            return ""

# 전역 인스턴스 생성 (어디서든 불러다 쓸 수 있게)
lore_book = LoreBook()