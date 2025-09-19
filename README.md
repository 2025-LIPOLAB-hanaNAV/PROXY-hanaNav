# hanaNav Proxy Server

FastAPI 기반 프록시 서버로 CORS 오류를 해결하고 PII Guard와 RAGFlow API를 중계합니다.

## 설치 및 실행

1. 가상환경 생성 및 활성화:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. 패키지 설치:
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

4. 서버 실행:
```bash
python main.py
```

또는 uvicorn으로 직접 실행:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API 엔드포인트

- `GET /health` - 헬스 체크
- `POST /api/pii/guard` - PII Guard 프록시
- `/api/ragflow/*` - RAGFlow API 프록시 (모든 HTTP 메소드 지원)

## 환경 변수

- `RAGFLOW_BASE_URL`: RAGFlow 서버 URL (기본값: http://zipbuntu.iptime.org)
- `RAGFLOW_API_KEY`: RAGFlow API 키
- `PII_GUARD_URL`: PII Guard 서버 URL (기본값: http://localhost:3000)
- `PORT`: 프록시 서버 포트 (기본값: 8000)
