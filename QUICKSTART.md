# Quick Start Guide 🚀

5분 안에 Notion Knowledge Agent 시작하기!

## 1. 환경 설정 (2분)

### Python 가상환경

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### API 키 설정

1. `.env.example`을 `.env`로 복사:
   ```bash
   cp .env.example .env
   ```

2. `.env` 파일 편집:
   ```env
   NOTION_API_KEY=secret_your_notion_key
   ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
   ```

## 2. Notion 연동 (1분)

1. [Notion Integrations](https://www.notion.so/my-integrations) 접속
2. "+ New integration" 클릭
3. 이름 입력 후 생성
4. "Internal Integration Token" 복사 → `.env`에 붙여넣기
5. Notion 페이지에서 "..." → "Add connections" → 통합 연결

## 3. 첫 동기화 (1분)

```bash
python cli.py sync --days 1
```

또는 Python으로:

```python
from src.sync.daily_sync import run_daily_sync

result = run_daily_sync(days=1)
print(result)
```

## 4. 대시보드 실행 (1분)

```bash
streamlit run src/dashboard/streamlit_app.py
```

브라우저에서 `http://localhost:8501` 자동 오픈!

## 5. 사용 시작!

### CLI로 사용

```bash
# 대화형 채팅
python cli.py chat

# 작업공간 분석
python cli.py analyze

# 주간 보고서 생성
python cli.py report weekly

# 자동 스케줄러 시작
python cli.py scheduler --start
```

### Python 코드로 사용

```python
from src.agents.notion_agent import create_agent

# 에이전트 생성
agent = create_agent()

# 질문하기
response = agent.chat("최근 작성한 문서 요약해줘")
print(response)

# 보고서 생성
report = agent.generate_report("weekly")
print(report)
```

### Streamlit 대시보드

1. **Overview**: 전체 현황 확인
2. **Chat**: AI와 대화
3. **Analytics**: 사용 패턴 분석
4. **Reports**: 보고서 생성
5. **Settings**: 개인화 설정
6. **Sync**: 동기화 관리

## 자주 묻는 질문

### Q: Notion API 오류가 나요
A:
1. API 키가 올바른지 확인
2. Notion 페이지에 통합이 연결되어 있는지 확인
3. 공개(Public) 페이지는 지원 안 됨 - 반드시 통합 연결 필요

### Q: 임베딩 모델 다운로드가 느려요
A: 처음 실행 시 약 90MB 모델 다운로드 필요 (1회만)

### Q: 벡터 DB 오류가 나요
A: `data/vector_db` 폴더 권한 확인

### Q: 자동 동기화 설정 방법은?
A:
```bash
# 스케줄러 시작
python cli.py scheduler --start

# 또는 대시보드에서 "Sync" 페이지에서 "스케줄러 시작" 버튼 클릭
```

## 다음 단계

- 📖 [전체 README](README.md) 읽기
- 🎨 Settings에서 보고서 스타일 커스터마이징
- 🤖 에이전트와 대화하며 작업공간 탐색
- 📊 Analytics에서 패턴 확인

## 문제 해결

문제가 있으면 이슈로 등록해주세요!

Happy knowledge managing! 📚✨
