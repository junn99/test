# 검증 가이드

프로젝트가 올바르게 설정되었는지 확인하는 방법입니다.

## 빠른 검증

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 기본 테스트 실행

```bash
python test_basic.py
```

모든 테스트가 통과하면 ✅ 마크가 표시됩니다.

## 예상 출력

```
============================================================
Notion Knowledge Agent - Basic Tests
============================================================
Testing imports...
  ✅ Config import OK
  ✅ Logger import OK
  ✅ Rate limiter import OK
  ✅ Cache import OK
  ✅ Notion tools import OK
  ✅ Analysis tools import OK
  ✅ User profile import OK
  ✅ Vector store import OK
  ✅ Sync import OK
  ✅ Style agent import OK
  ✅ Notion agent import OK
  ✅ Multi-agent import OK

Testing toolkit creation...
  ✅ Notion toolkit created with 8 tools
  ✅ All tools are properly structured
  ✅ Analysis toolkit created with 5 tools
  ✅ All analysis tools are properly structured

Testing user profile...
  ✅ User profile read/write OK

Testing cache...
  ✅ Cache operations OK
  ✅ Cache expiry OK

============================================================
✅ ALL TESTS PASSED!

Next steps:
1. Set up .env file with API keys
2. Run: streamlit run src/dashboard/streamlit_app.py
3. Or: python cli.py sync --days 1
============================================================
```

## 주요 수정 사항 (2025-11-18)

### 문제 발견 및 수정

**문제**: `@tool` 데코레이터가 인스턴스 메서드에 잘못 사용됨

- LangChain의 `@tool` 데코레이터는 일반 함수용
- 인스턴스 메서드에 사용 시 `self` 바인딩 문제 발생
- ToolNode에서 호출 불가

**해결**: `StructuredTool.from_function()` 사용

```python
# Before (잘못됨)
class NotionToolkit:
    @tool
    def get_all_pages(self):
        ...

# After (올바름)
class NotionToolkit:
    def get_all_pages(self):
        ...

    def get_tools(self):
        return [
            StructuredTool.from_function(
                func=self.get_all_pages,
                name="get_all_pages",
                description="..."
            ),
            # ...
        ]
```

### 수정된 파일

1. `src/tools/notion_tools.py`
   - `@tool` 데코레이터 제거 (7개)
   - `get_tools()` 메서드를 `StructuredTool` 사용하도록 수정
   - Import 변경: `tool` → `StructuredTool`

2. `src/tools/analysis_tools.py`
   - `@tool` 데코레이터 제거 (5개)
   - `get_tools()` 메서드를 `StructuredTool` 사용하도록 수정
   - Import 변경: `tool` → `StructuredTool`

## 개별 컴포넌트 테스트

### Notion Tools

```python
from src.tools.notion_tools import NotionToolkit

toolkit = NotionToolkit()
tools = toolkit.get_tools()
print(f"Tools: {len(tools)}")  # Should be 8

# Check tool structure
from langchain_core.tools import StructuredTool
for tool in tools:
    assert isinstance(tool, StructuredTool)
    print(f"✅ {tool.name}")
```

### Analysis Tools

```python
from src.tools.analysis_tools import ContentAnalyzer

analyzer = ContentAnalyzer()
tools = analyzer.get_tools()
print(f"Tools: {len(tools)}")  # Should be 5

for tool in tools:
    print(f"✅ {tool.name}")
```

### User Profile

```python
from src.memory.user_profile import UserProfile

profile = UserProfile()
profile.set_preference("test", "value")
assert profile.get_preference("test") == "value"
print("✅ User profile working")
```

### Cache

```python
from src.utils.cache import get_cache

cache = get_cache()
cache.set("key", "value", ttl=60)
assert cache.get("key") == "value"
print("✅ Cache working")
```

## 실제 사용 테스트

### 1. 환경 설정

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. 간단한 동기화 테스트

```bash
python cli.py sync --days 1
```

### 3. 대시보드 실행

```bash
streamlit run src/dashboard/streamlit_app.py
```

### 4. 멀티 에이전트 채팅

```bash
python cli.py chat --multi-agent
```

## 문제 해결

### Import 에러

```bash
# 의존성 재설치
pip install --upgrade -r requirements.txt
```

### API 키 오류

- `.env` 파일이 존재하는지 확인
- `NOTION_API_KEY`와 `ANTHROPIC_API_KEY`가 설정되었는지 확인

### 벡터 DB 오류

```bash
# 데이터 디렉토리 권한 확인
ls -la data/

# 필요시 재생성
rm -rf data/vector_db/
mkdir -p data/vector_db/
```

## 성능 검증

### 도구 수

- Notion Tools: **8개** ✅
- Analysis Tools: **5개** ✅
- 총: **13개** LangChain Tools

### 에이전트

- Basic Agent ✅
- Style Learning Agent ✅
- Multi-Agent System (4개 에이전트) ✅

### 통합

- Streamlit Dashboard (6 pages) ✅
- CLI (7 commands) ✅
- MCP Server ✅

## 완료 확인

모든 항목이 ✅이면 시스템이 올바르게 작동합니다:

- [ ] `test_basic.py` 모든 테스트 통과
- [ ] Import 에러 없음
- [ ] Tools 올바르게 생성됨 (StructuredTool)
- [ ] 캐시 작동 확인
- [ ] 사용자 프로필 작동 확인

---

**참고**: 실제 Notion API 호출은 `.env` 파일에 유효한 API 키가 있어야 합니다.
