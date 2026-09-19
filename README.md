# Busan Mate Prototype

부산 맞춤형 장소 추천 서비스의 API/추천 알고리즘 통합 프로토타입입니다.

## Prototype goal

- Local Ollama/Gemma로 자연어 질의를 구조화된 Intent JSON으로 변환
- Kakao와 Naver 장소 검색 Provider를 병렬 호출할 수 있는 구조 구성
- 한국관광공사 TourAPI와 기상청 API를 공공데이터포털 인증키 하나로 연결
- 서로 다른 Provider 결과를 공통 Place 모델로 정규화
- 중복 장소를 통합하고 자체 RecommendationService로 순위 계산
- 각 단계의 처리시간을 측정해 API/LLM 지연시간 비교

## Architecture

```
Chat GUI (app/static)
↓  POST /api/v1/recommend  { "message": "서면에서 친구랑 카페 추천해줘" }
FastAPI
↓
OllamaIntentParser (Gemma, JSON Schema + Pydantic 검증 + 재시도)
↓  UserIntent (requests[])
RecommendationPipeline  ── requests마다 병렬 처리
  ↓
  API Router ── Mock / Kakao / Naver / Tour (Timeout, 상태 기록)
  ↓
  PlaceMerger
  ↓
  RecommendationService
↓
요청별 TOP N + Provider 상태 + 단계별 처리시간

WeatherProvider
└─ PUBLIC_DATA_API_KEY + KMA_API_URL
```

## API environment variables

실제 키는 `.env`에만 넣고 Git에는 커밋하지 않습니다.

```env
KAKAO_REST_API_KEY=

NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

# TourAPI와 기상청이 공통으로 사용하는 공공데이터포털 인증키
PUBLIC_DATA_API_KEY=

TOUR_API_URL=
KMA_API_URL=
```

`PUBLIC_DATA_API_KEY`는 공공데이터포털에서 발급받은 일반 인증키 하나만 입력합니다.
TourAPI와 기상청 API는 같은 인증키를 사용하되, 서로 다른 Endpoint인 `TOUR_API_URL`과 `KMA_API_URL`로 구분합니다.

## Current stage

- 간단한 채팅형 GUI 추가 (로그인 없음, 대화 목록은 브라우저 localStorage에만 저장)
- 자연어 → Ollama Intent 해석 → 추천 흐름 연결
- Kakao/Naver 실제 장소 검색 Provider 연결
- TourAPI/기상청은 인증키와 URL 설정 구조까지 준비되어 있으며, 실제 API별 요청 파라미터/응답 필드 매핑은 연결 작업이 남아 있음
- `USE_MOCK_PLACES=true`이면 `[샘플]` 장소로 GUI와 점수 흐름을 확인 가능

## Run (Mac mini)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

ollama pull gemma4:e4b      # 처음 한 번
ollama serve                # Ollama 앱이 이미 실행 중이면 생략

python -m uvicorn app.main:app --reload
```

브라우저에서 http://127.0.0.1:8000 을 열면 채팅 화면이 나옵니다.
같은 네트워크의 다른 기기에서 열려면 `--host 0.0.0.0`을 붙이고 `http://<Mac mini IP>:8000`으로 접속합니다.
Ollama는 localhost로만 열어두면 됩니다.

Windows PowerShell에서는 `.venv\Scripts\Activate.ps1`을 사용합니다.

API 키가 들어가는 `.env`는 Git에 커밋하지 않습니다.

## Endpoints

| Method | Path | 용도 |
|---|---|---|
| GET | `/` | 채팅 GUI |
| GET | `/api/v1/status` | Ollama 연결, 모델 설치, Provider 키 설정 상태 |
| POST | `/api/v1/recommend` | 자연어 → Intent → 추천 (GUI가 사용) |
| POST | `/api/v1/intent` | 자연어 → Intent만 반환 (프롬프트 테스트) |
| POST | `/api/v1/recommend/intent` | 완성된 Intent → 추천 (LLM 없이 디버깅) |

자세한 요청 형식은 http://127.0.0.1:8000/docs 에서 확인합니다.

## Troubleshooting

- GUI에 "Ollama 연결 안 됨": `ollama serve` 실행 여부와 `OLLAMA_URL`을 확인합니다.
- "모델 없음": `ollama pull gemma4:e4b` 후 `OLLAMA_MODEL` 값과 태그가 같은지 확인합니다.
- Intent 호출 시 Ollama가 format 관련 오류를 반환: `.env`에서 `OLLAMA_STRUCTURED_OUTPUT=false`로 바꾸면 일반 JSON 모드로 호출합니다.
- 첫 요청만 느림: 모델 로딩 시간입니다. 서버 시작 시 백그라운드로 워밍업하고, `OLLAMA_KEEP_ALIVE` 동안 메모리에 유지합니다.
