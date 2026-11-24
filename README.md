# 게임 VOC 특징 분류 및 대응 지원 멀티에이전트 시스템

웹사이트, 전화상담, SNS에서 들어온 게임 VOC를 문제별로 묶고 문의량, 증가 추세와 심각도를 바탕으로 해결 우선순위를 제공하는 FastAPI 프로젝트입니다. SQLite에 원본 문의와 분석 이력을 누적합니다.

## 핵심 구성 요소

| 구성 요소 | 간략한 설명 |
| --- | --- |
| 고객 문의 화면 | 웹사이트 형식으로 VOC를 실시간 접수합니다. |
| 관리자 문의함 | 접수된 문의와 자동 분석 결과를 함께 확인합니다. |
| Agent A·B | VOC를 정제하고 유형별로 분류한 뒤 같은 문제끼리 묶습니다. |
| Agent C·D | 실제 피해 수준을 평가하고 해결 우선순위를 계산합니다. |
| FastAPI·SQLite | API 처리와 원본·분석 결과의 누적 저장을 담당합니다. |
| 테스트 | 분류, 그룹화, 심각도, 우선순위와 화면 경로를 검증합니다. |
| 발표자료 | [`VOC_멀티에이전트_발표자료_최종제출본.pptx`](deliverables/VOC_멀티에이전트_발표자료_최종제출본.pptx)에서 전체 흐름과 시연 결과를 확인할 수 있습니다. |

## 처리 구조

1. Agent A(수집·정제)가 채널을 표준화하고 개인정보를 마스킹합니다.
2. Agent B(분류·그룹화)가 유사 문의를 실제 문제 단위로 묶습니다.
3. Agent C(심각도 평가)가 기능 영향, 피해 유형, 복구 가능성과 시간 민감도를 계산합니다.
4. Agent D(우선순위 결정)가 문의량, 증가 추세와 심각도를 종합합니다.

네 역할의 상세 책임과 입출력 기준은 `prompts/README.md`와 `prompts/agent_a_*.md`부터 `agent_d_*.md`까지의 파일에 정리되어 있습니다.

현재는 고객 문의 접수 화면, 관리자 실시간 문의함, 문제별 그룹화, 심각도 평가, 해결 우선순위 계산 API와 관리자 대시보드를 제공합니다.

## CMD 실행 방법

프로젝트 폴더로 이동합니다.

```cmd
cd /d D:\LLM\voc_multi_agent
```

가상환경을 활성화합니다.

```cmd
.venv\Scripts\activate
```

필요한 경우에만 현재 프로젝트 버전에 맞춰 패키지를 설치합니다.

```cmd
python -m pip install -r requirements.txt
```

기본 데이터베이스 파일은 `data\game_voc.db`입니다. 다른 위치를 사용하려는 경우에만 `.env`에 다음 값을 추가합니다.

```env
SQLITE_DATABASE_PATH=data/game_voc.db
```

SQLite는 별도 서버, 계정 또는 비밀번호가 필요하지 않습니다.

FastAPI 개발 서버를 실행합니다.

```cmd
python main.py
```

다음 주소에서 고객 화면, 관리자 화면, API 문서와 상태를 확인합니다.

```text
http://127.0.0.1:8000/voc
http://127.0.0.1:8000/admin
http://127.0.0.1:8000/admin/inbox
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
http://127.0.0.1:8000/health/database
```

원본 VOC API:

```text
POST /api/v1/vocs
POST /api/v1/vocs/intake
POST /api/v1/vocs/bulk
GET  /api/v1/vocs
GET  /api/v1/vocs/{voc_id}
GET  /api/v1/admin/vocs
GET  /api/v1/admin/vocs/{voc_id}
POST /api/v1/analysis/classify
GET  /api/v1/issues
GET  /api/v1/issues/{group_id}
POST /api/v1/priorities/recalculate
GET  /api/v1/priorities
```

## SQLite 초기 설정

FastAPI를 시작하면 필요한 테이블을 자동으로 생성합니다. 서버 실행 전에 직접 초기화하고 구조를 확인하려면 다음 명령을 실행합니다.

```cmd
python -m scripts.init_sqlite
```

정상 실행되면 다음 파일과 테이블 5개가 생성됩니다.

```text
data\game_voc.db
vocs
voc_analyses
issue_groups
voc_issue_links
issue_priorities
```

테스트를 실행합니다.

```cmd
python -m unittest discover -s tests -v
```

## 발표용 데이터와 전체 흐름 실행

SQLite에 시연용 VOC 40건을 저장하고 분류, 문제 그룹화와 우선순위 계산을 연속 실행합니다.

```cmd
python -m scripts.seed_demo_data
```

진행 상황과 최종 순위가 CMD에 한글로 표시되며 결과는 다음 파일에도 저장됩니다.

```text
outputs\demo_priority_result.json
```

동일한 명령을 다시 실행해도 기존 시연 데이터는 중복 등록되지 않으며 우선순위만 다시 계산됩니다.

## 프로젝트 폴더 구조

```text
app/
├─ api/           FastAPI 엔드포인트
├─ core/          환경 설정
├─ db/            SQLite 연결과 ORM 모델
├─ repositories/  데이터 조회·저장
├─ schemas/       요청·응답 데이터 형식
├─ services/      수집, 분류, 심각도와 우선순위 로직
├─ static/        고객·관리자 화면 CSS·JavaScript
└─ web/           고객 문의, 관리자 대시보드와 문의함 HTML
voc_system/       개인정보 마스킹과 분류 규칙
prompts/          Agent A~D의 역할과 입출력 기준
scripts/          DB 초기화, 데모 데이터와 검증 명령
tests/            핵심 규칙과 화면 경로 테스트
data/             SQLite 데이터베이스
outputs/          데모 우선순위 결과 JSON
deliverables/     최종 발표 자료
```

## FastAPI VOC 입력 형식

`POST /api/v1/vocs` 요청 본문은 다음 형식입니다.

```json
{
  "external_id": "VOC-001",
  "channel": "website",
  "content": "결제가 중복으로 됐습니다.",
  "received_at": "2026-11-17T09:15:00+09:00",
  "game_name": "Project Arena",
  "platform": "Windows",
  "game_version": "1.0.0",
  "metadata": {"source": "demo"}
}
```

여러 건을 한 번에 등록할 때는 `POST /api/v1/vocs/bulk`의 `items` 배열에 같은 형식의 객체를 넣습니다. `received_at`에는 `+09:00` 또는 `Z` 같은 시간대 정보가 반드시 필요합니다.

## 관리자 대시보드 기능

- 누적 VOC와 문제 그룹 수 확인
- P0·P1 긴급 대응 문제 수 확인
- 최근 7일과 직전 7일의 문의량 비교
- 심각도, 문의량과 증가 추세를 반영한 해결 순위 조회
- 미분석 VOC 분류와 우선순위 재계산 실행
- 사이드바에서 대시보드, 실시간 문의함, 순위와 분석 기준 이동
- 방금 접수된 문의의 고객 작성 내용과 처리 결과 확인
- 유입 채널, 분류 유형, 문제 그룹, 심각도와 최종 순위 확인

## 실시간 시연 방법

1. 고객 역할로 `http://127.0.0.1:8000/voc`에 접속합니다.
2. 게임과 플랫폼을 선택하고 문의 내용을 작성한 뒤 `문의 전송`을 누릅니다.
3. `문의가 정상적으로 접수되었습니다.` 안내와 접수번호를 확인합니다.
4. 관리자 역할로 `http://127.0.0.1:8000/admin/inbox`에 접속합니다.
5. `방금 접수` 표시가 있는 문의를 선택해 고객이 작성한 내용과 자동 분석 결과를 확인합니다.
6. `http://127.0.0.1:8000/admin`에서 전체 VOC 수, 문의 유형별 분포와 해결 우선순위 변화를 확인합니다.

기본 예시 문장은 다음과 같습니다.

```text
게임 로그인을 하고 게임 실행을 했는데 게임이 팅겨요
```

이 문장은 `기술 오류 > 강제 종료`로 분류되어 기존 강제 종료 문제 그룹에 합쳐집니다. 처리 후 전체 VOC 수와 해당 그룹의 문의량이 즉시 증가합니다.

## 실제 서비스로 확장할 때 권장하는 순서

- 실제 웹사이트·전화상담·SNS 채널 API 연결
- 상담원이 이슈 상태를 변경하는 운영 기능
- 급증 이슈 알림과 담당자 통지
- 답변 결과와 재문의율을 이용한 품질 평가
- 운영정책을 반영한 분류·심각도 기준 검수

현재 버전은 설계와 시연을 위한 로컬 프로토타입입니다. 실제 환불, 계정 제재, 보상 지급은 수행하지 않습니다.

