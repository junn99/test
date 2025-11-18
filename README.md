# Email Assistant Agent 📧

회사 내부용 이메일 어시스턴트 에이전트입니다. LangChain과 Streamlit을 활용하여 Gmail 이메일 관리를 자동화합니다.

## ✨ v1.1 업데이트 (2024-11-18)

**새로운 기능:**
- 📝 **이메일 템플릿 시스템**: 자주 쓰는 이메일을 템플릿으로 저장하고 재사용
- ⚡ **배치 작업**: 여러 이메일을 한 번에 처리 (읽음 표시, 삭제, 보관 등)
- 🎯 **개선된 AI 프롬프트**: 더 정확하고 맥락을 이해하는 응답

자세한 내용은 [IMPROVEMENTS.md](./IMPROVEMENTS.md)를 참조하세요.

## 주요 기능

### 🔍 이메일 확인
- 받은 편지함 조회
- 읽지 않은 메일 필터링
- 메일 검색 (발신자, 제목, 날짜 등)
- 메일 상세 내용 표시

### 🔔 이메일 알림
- 실시간 새 메일 확인
- 중요 메일 감지
- 맞춤 알림 규칙

### ✍️ 이메일 초안 작성
- AI 기반 이메일 초안 생성
- 다양한 톤/스타일 선택 (전문적, 캐주얼, 친근함, 공식적)
- 컨텍스트 기반 답장 생성

### 📤 자동 발송
- 초안 검토 후 자동 발송
- 대량 발송 지원
- 발송 이력 관리

### 🤖 AI 에이전트 채팅
- 자연어로 이메일 작업 수행
- 이메일 요약 및 분석
- 질의응답

### 📝 이메일 템플릿 (NEW!)
- 자주 쓰는 이메일을 템플릿으로 저장
- 변수 시스템으로 맞춤 작성
- 카테고리별 분류
- 기본 템플릿 5개 제공

### ⚡ 배치 작업 (NEW!)
- 여러 이메일 일괄 처리
- 읽음/읽지않음 표시
- 별표, 보관, 삭제
- 작업 결과 상세 보고

## 기술 스택

- **Frontend**: Streamlit
- **AI Framework**: LangChain v1.0
- **Email API**: Gmail API
- **LLM**: OpenAI GPT / Anthropic Claude
- **Language**: Python 3.9+

## 프로젝트 구조

```
email-assistant-agent/
├── app.py                      # Streamlit 메인 앱
├── requirements.txt            # 패키지 의존성
├── .env.example               # 환경 변수 예제
├── README.md                  # 프로젝트 문서
├── config/
│   ├── __init__.py
│   └── settings.py            # 설정 관리
├── agents/
│   ├── __init__.py
│   ├── email_agent.py         # LangChain 에이전트
│   └── tools.py               # 에이전트 도구들
├── services/
│   ├── __init__.py
│   ├── base_email.py          # 이메일 서비스 추상 클래스
│   └── gmail_service.py       # Gmail API 서비스
└── utils/
    ├── __init__.py
    ├── auth.py                # 인증 관련
    └── helpers.py             # 유틸리티 함수
```

## 설치 및 실행

### 1. 사전 준비

#### Gmail API 인증 설정
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. Gmail API 활성화
4. OAuth 2.0 클라이언트 ID 생성 (애플리케이션 유형: 데스크톱 앱)
5. `credentials.json` 파일 다운로드

#### LLM API 키 준비
- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: [https://console.anthropic.com/](https://console.anthropic.com/)

### 2. 환경 설정

```bash
# 저장소 클론 또는 프로젝트 디렉토리 이동
cd email-assistant-agent

# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env

# .env 파일 수정 (API 키 입력)
# OPENAI_API_KEY=your_openai_api_key_here
# 또는
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Gmail 인증 파일 설정

다운로드한 `credentials.json` 파일을 프로젝트 루트 디렉토리에 복사합니다.

```bash
# credentials.json을 프로젝트 루트에 배치
cp /path/to/downloaded/credentials.json .
```

### 4. 애플리케이션 실행

```bash
# Streamlit 앱 실행
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 앱에 접근할 수 있습니다.

### 5. 첫 실행 시 Gmail 인증

처음 실행하면 브라우저에서 Google 로그인 창이 열립니다:
1. Google 계정으로 로그인
2. 권한 요청 승인
3. 인증 완료 후 `token.json` 파일이 자동 생성됩니다

## 사용 방법

### 📬 Inbox (받은 편지함)
- 상단의 "Inbox" 메뉴 선택
- "Refresh" 버튼으로 최신 이메일 가져오기
- 필터 옵션으로 읽지 않은 메일만 보기
- 각 이메일 카드 확장하여 전체 내용 확인

### ✍️ Compose (이메일 작성)
- "Compose" 메뉴 선택
- 수신자, 제목, 본문 입력
- AI 톤/길이 선택
- "Generate with AI"로 AI 초안 생성
- "Save as Draft"로 초안 저장
- "Send Email"로 즉시 발송

### 🔍 Search (검색)
- "Search" 메뉤 선택
- Gmail 검색 문법 사용:
  - `from:example@gmail.com` - 특정 발신자
  - `subject:meeting` - 제목 키워드
  - `is:unread` - 읽지 않은 메일
  - `has:attachment` - 첨부파일 있는 메일
  - `after:2024/01/01` - 날짜 이후

### 🤖 Agent Chat (AI 채팅)
- "Agent Chat" 메뉴 선택
- 자연어로 요청:
  - "최근 읽지 않은 메일 10개 보여줘"
  - "오늘 온 메일 중 중요한 것만 요약해줘"
  - "John에게 회의 일정 변경 메일 작성해줘"

## 환경 변수 설정

`.env` 파일에서 다음 설정을 변경할 수 있습니다:

```env
# LLM 제공자 선택
LLM_PROVIDER=openai  # 또는 anthropic

# OpenAI 사용 시
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo-preview

# Anthropic 사용 시
# ANTHROPIC_API_KEY=sk-ant-...
# LLM_MODEL=claude-3-opus-20240229

# LLM 설정
LLM_TEMPERATURE=0.7
MAX_TOKENS=2000

# 이메일 설정
CHECK_INTERVAL_SECONDS=60
MAX_EMAILS_PER_FETCH=50
```

## Gmail 검색 문법

Gmail API는 강력한 검색 문법을 지원합니다:

| 쿼리 | 설명 |
|------|------|
| `from:user@example.com` | 특정 발신자의 메일 |
| `to:user@example.com` | 특정 수신자에게 보낸 메일 |
| `subject:meeting` | 제목에 "meeting" 포함 |
| `is:unread` | 읽지 않은 메일 |
| `is:starred` | 별표 표시된 메일 |
| `has:attachment` | 첨부파일이 있는 메일 |
| `after:2024/01/01` | 특정 날짜 이후 |
| `before:2024/12/31` | 특정 날짜 이전 |
| `label:work` | 특정 라벨의 메일 |

## 보안 고려사항

- **API 키 보호**: `.env` 파일을 절대 공유하거나 커밋하지 마세요
- **Gmail 인증**: OAuth 2.0을 사용하여 안전하게 인증
- **토큰 관리**: `token.json` 파일도 `.gitignore`에 포함됨
- **권한 최소화**: 필요한 Gmail 스코프만 요청

## 문제 해결

### Gmail 인증 오류
```
FileNotFoundError: credentials.json not found
```
**해결**: Google Cloud Console에서 `credentials.json` 다운로드 후 프로젝트 루트에 배치

### LLM API 오류
```
OpenAI API key not configured
```
**해결**: `.env` 파일에 `OPENAI_API_KEY` 또는 `ANTHROPIC_API_KEY` 설정

### 권한 거부 오류
```
Error 403: Access Denied
```
**해결**: Gmail API가 Google Cloud Console에서 활성화되었는지 확인

### 인증 재설정
인증 문제 발생 시:
1. `token.json` 삭제
2. 앱 재시작
3. 다시 Gmail 로그인 진행

## 향후 개선 사항

- [ ] Microsoft Outlook 지원
- [ ] 이메일 템플릿 시스템
- [ ] 예약 발송 기능
- [ ] 첨부파일 관리
- [ ] 다국어 지원
- [ ] 이메일 분석 대시보드
- [ ] 자동 분류 및 레이블링
- [ ] 팀 공유 기능

## 라이선스

MIT License

## 기여

버그 리포트, 기능 제안, PR 환영합니다!

## 지원

문제가 발생하면 Issue를 생성해주세요.

---

**Made with ❤️ using LangChain & Streamlit**
