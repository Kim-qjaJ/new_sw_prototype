# Busan Mate Prototype

부산 맞춤형 장소 추천 서비스의 API/추천 알고리즘 통합 프로토타입입니다.

## Prototype goal

1. Local Ollama/Gemma로 자연어 질의를 구조화된 Intent JSON으로 변환
2. Kakao와 Naver 장소 검색 Provider를 병렬 호출할 수 있는 구조 구성
3. 부산 공공데이터, 관광, 날씨 Provider를 독립 모듈로 확장
4. 서로 다른 Provider 결과를 공통 `Place` 모델로 정규화
5. 중복 장소를 통합하고 자체 RecommendationService로 순위 계산
6. 각 단계의 처리시간을 측정해 API/LLM 지연시간 비교

## Architecture

```text
User
  ↓
FastAPI
  ↓
Gemma / Ollama → UserIntent
  ↓
API Router
  ├─ KakaoProvider
  ├─ NaverProvider
  ├─ BusanProvider
  ├─ TourProvider
  └─ WeatherProvider
  ↓
PlaceNormalizer / PlaceMerger
  ↓
RecommendationService
  ↓
TOP N Places + timing
```

## Current stage

현재는 프로토타입 뼈대 단계입니다. Provider 인터페이스와 추천 모델을 먼저 고정하고 실제 API는 하나씩 연결합니다.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

Windows PowerShell에서는 `.venv\\Scripts\\Activate.ps1`을 사용합니다.

API 키가 들어가는 `.env`는 Git에 커밋하지 않습니다.
