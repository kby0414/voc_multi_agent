"""Windows CMD에서 FastAPI 개발 서버를 실행한다."""

import uvicorn


if __name__ == "__main__":
    print("=" * 68, flush=True)
    print("게임 VOC 이슈 우선순위 분석 시스템을 시작합니다.", flush=True)
    print("고객 문의   : http://127.0.0.1:8000/voc", flush=True)
    print("관리자 화면 : http://127.0.0.1:8000/admin", flush=True)
    print("실시간 문의 : http://127.0.0.1:8000/admin/inbox", flush=True)
    print("API 문서    : http://127.0.0.1:8000/docs", flush=True)
    print("종료        : Ctrl+C", flush=True)
    print("=" * 68, flush=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
