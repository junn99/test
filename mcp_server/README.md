# Notion Knowledge Agent - MCP Server

Claude Desktop과 통합하기 위한 MCP (Model Context Protocol) 서버입니다.

## 기능

- 🔍 **Notion 검색**: 작업공간에서 페이지 검색
- 📄 **페이지 읽기**: 전체 페이지 콘텐츠 가져오기
- ✍️ **페이지 생성**: 새 Notion 페이지 생성
- 📊 **작업공간 분석**: AI 기반 분석 및 인사이트
- 📝 **보고서 생성**: 학습된 스타일로 보고서 자동 생성
- 🤖 **멀티 에이전트 질의**: 전문화된 AI 에이전트에게 질문

## 설치

### 1. 프로젝트 설정

```bash
cd /path/to/notion-knowledge-agent
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일에 API 키 설정:

```env
NOTION_API_KEY=your_notion_integration_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 3. Claude Desktop 설정

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

다음 내용을 추가하거나 병합:

```json
{
  "mcpServers": {
    "notion-knowledge-agent": {
      "command": "python",
      "args": [
        "/absolute/path/to/notion-knowledge-agent/mcp_server/server.py"
      ],
      "env": {
        "NOTION_API_KEY": "secret_xxxxx",
        "ANTHROPIC_API_KEY": "sk-ant-xxxxx"
      }
    }
  }
}
```

**주의**: 경로를 절대 경로로 변경하세요!

### 4. Claude Desktop 재시작

설정을 적용하려면 Claude Desktop을 완전히 종료하고 다시 시작하세요.

## 사용 방법

Claude Desktop에서 다음과 같이 사용:

### Notion 검색
```
노션에서 "프로젝트 계획" 검색해줘
```

### 페이지 읽기
```
페이지 ID xxx의 내용을 보여줘
```

### 페이지 생성
```
"회의 노트"라는 제목으로 새 페이지를 만들어줘
내용: 오늘 회의 내용 정리...
```

### 작업공간 분석
```
내 노션 작업공간을 분석해줘
```

### 보고서 생성
```
이번 주 작업 내용으로 보고서를 만들어줘
```

### AI 에이전트 질의
```
최근 문서들의 주요 패턴과 키워드를 분석해줘
```

## 사용 가능한 도구

| 도구 | 설명 |
|------|------|
| `search_notion` | Notion에서 페이지 검색 |
| `get_page` | 페이지 전체 콘텐츠 가져오기 |
| `create_page` | 새 페이지 생성 |
| `analyze_workspace` | 작업공간 분석 |
| `generate_report` | 맞춤형 보고서 생성 |
| `ask_agent` | 멀티 에이전트 시스템에 질문 |

## 문제 해결

### MCP 서버가 연결되지 않음

1. Claude Desktop을 완전히 종료하고 재시작
2. 설정 파일 경로가 올바른지 확인
3. Python 경로가 올바른지 확인
4. 환경 변수가 올바르게 설정되었는지 확인

### 로그 확인

```bash
# 서버를 수동으로 실행해서 오류 확인
python mcp_server/server.py
```

### API 키 오류

- Notion API 키가 올바른지 확인
- Notion 통합이 페이지에 연결되어 있는지 확인
- Anthropic API 키가 유효한지 확인

## 개발자 정보

### MCP 서버 테스트

```bash
# 서버 시작
python mcp_server/server.py

# 다른 터미널에서 테스트 요청 전송
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python mcp_server/server.py
```

### MCP 프로토콜

이 서버는 Model Context Protocol (MCP)를 구현합니다:
- JSON-RPC 2.0 프로토콜
- stdio를 통한 통신
- Tools, Resources, Prompts 지원

## 라이선스

MIT License
