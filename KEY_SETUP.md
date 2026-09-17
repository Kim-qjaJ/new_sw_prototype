# API Key setup

실제 API 키는 GitHub에 커밋하지 않고 프로젝트 루트의 `.env` 파일에만 저장합니다.

필수 키:

```env
KAKAO_REST_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
PUBLIC_DATA_API_KEY=
```

`PUBLIC_DATA_API_KEY`는 공공데이터포털의 일반 인증키 1개를 공통으로 사용하도록 구성했습니다. Encoding/Decoding 키 어느 쪽을 넣어도 내부에서 URL decoding을 한 번 적용합니다.

공공데이터포털 API는 인증키만으로 어떤 데이터셋을 호출할지 알 수 없으므로, 실제로 사용할 부산/관광/날씨 API의 요청 URL은 별도로 연결해야 합니다. 현재는 아래 항목을 선택적으로 둘 수 있습니다.

```env
BUSAN_API_URL=
TOUR_API_URL=
KMA_API_URL=
```

Kakao/Naver 장소 검색은 키를 넣고 `USE_MOCK_PLACES=false`로 설정하면 바로 실제 검색 Provider가 호출됩니다.
