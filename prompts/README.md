# 멀티에이전트 역할

| 코드 | 프롬프트 | 책임 | 구현 방식 |
| --- | --- | --- | --- |
| Agent A | `agent_a_collector.md` | 채널 표준화, 개인정보 마스킹, 문의 요약 | 규칙 기반, 선택적 AI 보강 |
| Agent B | `agent_b_classifier.md` | 카테고리·토픽 분류, 유사 문의 그룹화 | 규칙 기반, 선택적 AI 보강 |
| Agent C | `agent_c_severity.md` | 기능 영향·피해·복구·시간 민감도 평가 | 설명 가능한 고정 점수표 |
| Agent D | `agent_d_priority.md` | 심각도·문의량·증가 추세 종합 및 순위 결정 | 설명 가능한 고정 산식 |

현재 기본 실행 모드는 외부 API 없이 재현 가능한 규칙 기반 방식입니다. `OPENAI_API_KEY`와 AI 모드를 사용할 때만 Agent A와 B의 결과를 프롬프트로 보강합니다. Agent C와 D는 발표와 운영 검증에서 같은 입력에 같은 결과를 내도록 고정 규칙을 사용합니다.
