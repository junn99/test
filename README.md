# Notion Knowledge Agent 📚

LangChain과 LangGraph를 활용한 노션 개인 지식 관리 AI 에이전트입니다.

## 주요 기능

- 🤖 **AI 에이전트**: LangGraph 기반 멀티 에이전트 시스템
- 🔍 **RAG 검색**: 벡터 데이터베이스를 활용한 의미 기반 검색
- 📊 **작업공간 분석**: 사용 패턴, 키워드, 태그 자동 학습
- 📝 **자동 보고서**: 개인화된 스타일로 주간/월간 보고서 생성
- 🔄 **자동 동기화**: 매일 자동으로 노션 콘텐츠 동기화
- 💬 **대화형 인터페이스**: Streamlit 기반 웹 대시보드
- 🎨 **스타일 학습**: 사용자의 글쓰기 스타일 학습 및 적용

## 아키텍처

```
notion-knowledge-agent/
├── src/
│   ├── agents/              # LangGraph 에이전트
│   ├── tools/               # Notion API Tools
│   ├── rag/                 # RAG 시스템 (Vector DB + Embeddings)
│   ├── sync/                # 동기화 로직
│   ├── scheduler/           # 백그라운드 스케줄러
│   ├── memory/              # 사용자 프로필 & 메모리
│   ├── dashboard/           # Streamlit UI
│   └── utils/               # 설정 & 유틸리티
├── data/
│   ├── vector_db/           # ChromaDB 벡터 저장소
│   ├── profiles/            # 사용자 프로필
│   └── cache/               # 캐시
└── prompts/
    └── templates/           # 보고서 템플릿
```

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd notion-knowledge-agent
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example`을 `.env`로 복사하고 필요한 값을 입력하세요:

```bash
cp .env.example .env
```

`.env` 파일 예시:

```env
# Notion API
NOTION_API_KEY=secret_xxxxxxxxxxxxx
NOTION_WORKSPACE_ID=your_workspace_id

# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# LangSmith (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=notion-knowledge-agent

# Vector Database
VECTOR_DB_PATH=./data/vector_db
VECTOR_DB_TYPE=chromadb

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Sync Schedule
SYNC_HOUR=4
SYNC_TIMEZONE=Asia/Seoul

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Notion API 키 발급 방법

1. [Notion Developers](https://www.notion.so/my-integrations) 페이지 접속
2. "+ New integration" 클릭
3. 통합 이름 입력 및 권한 설정
4. "Submit" 후 "Internal Integration Token" 복사
5. Notion 페이지에서 "..." → "Add connections" → 생성한 통합 연결

## Anthropic API 키 발급

1. [Anthropic Console](https://console.anthropic.com/) 접속
2. "API Keys" 메뉴에서 새 키 생성
3. 생성된 키를 `.env` 파일에 추가

## 사용 방법

### Streamlit 대시보드 실행

```bash
streamlit run src/dashboard/streamlit_app.py
```

브라우저에서 자동으로 `http://localhost:8501` 열림

### 대시보드 기능

#### 🏠 Overview
- 작업공간 전체 개요
- 빠른 작업 버튼 (분석, 보고서 생성, 동기화)

#### 💬 Chat
- AI 비서와 대화형 인터페이스
- 노션 콘텐츠 검색 및 질문
- 자동 컨텍스트 검색 (RAG)

#### 📊 Analytics
- 자주 사용하는 키워드 분석
- 태그 사용 패턴
- 글쓰기 스타일 분석

#### 📝 Reports
- 일간/주간/월간 보고서 생성
- 개인화된 스타일 적용
- 마크다운 다운로드

#### ⚙️ Settings
- 보고서 스타일 설정
- 언어 톤 설정
- 사용자 프로필 관리

#### 🔄 Sync
- 수동 동기화 실행
- 자동 동기화 스케줄러 관리
- 동기화 히스토리

### Python 코드로 사용

```python
from src.agents.notion_agent import create_agent

# 에이전트 생성
agent = create_agent()

# 대화
response = agent.chat("최근에 작성한 문서 요약해줘")
print(response)

# 작업공간 분석
analysis = agent.analyze_workspace()
print(analysis)

# 보고서 생성
report = agent.generate_report("weekly")
print(report)
```

### 동기화 스크립트

```python
from src.sync.daily_sync import run_daily_sync, run_full_sync

# 최근 1일 동기화
result = run_daily_sync(days=1)
print(result)

# 전체 동기화
result = run_full_sync()
print(result)
```

## 동기화 전략

- **자동 동기화**: 매일 새벽 4시 (설정 변경 가능)
- **증분 동기화**: 변경된 페이지만 업데이트
- **벡터 DB 최적화**: 기존 벡터 삭제 후 재생성

## 기술 스택

- **LangChain v1.0**: 에이전트 프레임워크
- **LangGraph**: 멀티 에이전트 워크플로우
- **Anthropic Claude**: LLM (Claude 3.5 Sonnet)
- **Notion API**: 노션 데이터 연동
- **ChromaDB**: 벡터 데이터베이스
- **Sentence Transformers**: 임베딩 모델
- **Streamlit**: 웹 대시보드
- **APScheduler**: 백그라운드 작업 스케줄링

## 개발

### 테스트 실행

```bash
pytest tests/
```

### 코드 포맷팅

```bash
black src/
ruff check src/
```

## 로그

로그는 콘솔에 출력되며, `LOG_LEVEL` 환경 변수로 레벨 조정 가능:

```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 문제 해결

### Notion API 연결 오류
- API 키가 올바른지 확인
- Notion 페이지에 통합이 연결되어 있는지 확인

### 벡터 DB 오류
- `data/vector_db` 디렉토리 권한 확인
- 디스크 공간 확인

### 임베딩 모델 다운로드 느림
- 처음 실행 시 모델 다운로드 필요 (약 90MB)
- 인터넷 연결 확인

## 향후 계획

- [ ] MCP 서버 구현 (Claude Desktop 통합)
- [ ] 멀티 에이전트 협업 시스템
- [ ] 더 많은 보고서 템플릿
- [ ] 웹훅 지원 (실시간 동기화)
- [ ] 다국어 지원
- [ ] 노션 데이터베이스 쿼리 지원

## 라이선스

MIT License

## 기여

이슈 및 PR 환영합니다!

## 문의

문제가 있으시면 이슈를 등록해주세요.
