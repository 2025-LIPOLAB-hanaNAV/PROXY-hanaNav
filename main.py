from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Any, Dict
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JUNI Proxy Server", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 환경 변수에서 설정 읽기
RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://zipbuntu.iptime.org")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")
PII_GUARD_URL = os.getenv("PII_GUARD_URL", "http://localhost:3000")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "JUNI Proxy Server"}

@app.post("/api/pii/guard")
async def pii_guard_proxy(request: Request):
    """PII Guard 서비스로 프록시"""
    try:
        body = await request.json()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PII_GUARD_URL}/guard",
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )

            if response.status_code != 200:
                logger.error(f"PII Guard API error: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"PII Guard API 요청 실패: {response.status_code}"
                )

            return response.json()

    except httpx.TimeoutException:
        logger.error("PII Guard API timeout")
        raise HTTPException(status_code=504, detail="PII Guard 서비스 타임아웃")
    except httpx.RequestError as e:
        logger.error(f"PII Guard API connection error: {e}")
        raise HTTPException(status_code=503, detail="PII Guard 서비스에 연결할 수 없습니다")
    except Exception as e:
        logger.error(f"PII Guard proxy error: {e}")
        raise HTTPException(status_code=500, detail="PII Guard 프록시 오류")

@app.api_route("/api/ragflow/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def ragflow_proxy(path: str, request: Request):
    """RAGFlow API로 프록시"""
    try:
        # 요청 body 읽기 (있는 경우)
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                body = await request.body()

        # 쿼리 파라미터 가져오기
        query_params = dict(request.query_params)

        # 헤더 준비
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RAGFLOW_API_KEY}"
        }

        # 원본 요청의 일부 헤더 복사 (필요한 경우)
        for header_name in ["user-agent", "accept"]:
            if header_name in request.headers:
                headers[header_name] = request.headers[header_name]

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{RAGFLOW_BASE_URL}/api/{path}",
                json=body if isinstance(body, (dict, list)) else None,
                content=body if isinstance(body, bytes) else None,
                params=query_params,
                headers=headers,
                timeout=60.0
            )

            # 응답 헤더 준비
            response_headers = {}
            for header_name in ["content-type", "content-length"]:
                if header_name in response.headers:
                    response_headers[header_name] = response.headers[header_name]

            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=response_headers
            )

    except httpx.TimeoutException:
        logger.error(f"RAGFlow API timeout for path: {path}")
        raise HTTPException(status_code=504, detail="RAGFlow 서비스 타임아웃")
    except httpx.RequestError as e:
        logger.error(f"RAGFlow API connection error for path {path}: {e}")
        raise HTTPException(status_code=503, detail="RAGFlow 서비스에 연결할 수 없습니다")
    except Exception as e:
        logger.error(f"RAGFlow proxy error for path {path}: {e}")
        raise HTTPException(status_code=500, detail="RAGFlow 프록시 오류")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)