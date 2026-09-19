# DAEGU:IDE 프로토타입

대구 거주 외국인이 급여명세서, 임대차계약서, 공과금 고지서를 이해하고 다음 행동까지 이어갈 수 있도록 돕는 웹 프로토타입입니다.

## 구현 기능

- JPG, PNG, WEBP, PDF 업로드 및 최대 8MB 검증
- Gemini 멀티모달 기반 문서 유형, 요약, 핵심 금액, 날짜, 위험 조건, 후속 행동 추출
- 한국어, 영어, 중국어, 베트남어 UI 및 샘플 분석 결과
- 급여명세서, 임대차계약서, 공과금 고지서 샘플 체험
- 한국어 상담 요청문이 포함된 상담카드 생성과 복사
- 문서에서 찾은 날짜의 금융 캘린더 등록 UX 시연
- 대구 구·군과 문서 유형에 따른 규칙 기반 지원기관 추천
- 지도 검색과 공식 기관 사이트 연결
- 피싱 위험 신호와 AI 질문 UI 시연

## 현재 구현과 시연 기능 구분

| 기능 | 상태 | 비고 |
|---|---|---|
| 실제 파일 분석 | 구현 | Gemini API 호출 |
| 4개 언어 샘플 | 구현 | 저장된 분석 JSON 사용 |
| 상담카드 | 구현 | 한국어 요청문 복사 |
| 기관 추천 | 구현 | AI가 아닌 데이터·규칙 기반 |
| 금융 캘린더 | 시연 | 영구 저장과 푸시 알림 미구현 |
| 피싱 체크 | 시연 | 분류 모델 API 미연동 |
| AI 질문 | 시연 | 자유 질의 API 미연동 |

## 공개 데모 실행(Streamlit)

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

실제 문서 분석을 사용하려면 `.streamlit/secrets.toml`을 만들고 다음 값을 등록합니다.

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL = "gemini-2.5-flash"
```

`secrets.toml`과 실제 API 키는 GitHub 또는 제출 ZIP에 포함하지 않습니다. 키가 없어도 저장된 샘플 분석, 기관 추천, 상담카드, 금융 캘린더와 피싱 규칙 점검을 시연할 수 있습니다.

## 기술 구성

- Public demo: Python, Streamlit, custom HTML/CSS
- Original frontend: HTML5, CSS3, Vanilla JavaScript
- Original backend: JavaScript Serverless Worker
- AI: Google Gemini multimodal API
- Data: JSON, XLSX, CSV
- Output control: JSON Schema
- Deployment: Streamlit Community Cloud / Cloudflare Workers-compatible environment

## 프로젝트 구조

```text
site/
  index.html
  styles.css
  app.js
  data/
    daeguide_document_analysis.json
    daeguide_multilingual_analysis_all.json
    daegu_support_centers.json
worker/
  template.js
scripts/
  build.mjs
  validate.mjs
dist/
  server/index.js
streamlit_app.py
requirements.txt
.streamlit/
  config.toml
  secrets.toml.example
```

## 실행 준비

Node.js 환경에서 다음 명령을 실행합니다.

```bash
npm run build
npm run validate
```

실제 업로드 분석에는 실행 환경의 비밀 변수로 `GEMINI_API_KEY`가 필요합니다. API 키는 제출 파일에 포함하지 않았습니다.

## 분석 API 흐름

1. 브라우저가 `/api/analyze`에 파일과 선택 언어를 `multipart/form-data`로 전송합니다.
2. Worker가 파일 형식과 8MB 용량 제한을 검사합니다.
3. Gemini 멀티모달 모델이 이미지 또는 PDF를 읽습니다.
4. JSON Schema에 맞춰 문서 유형, 요약, 핵심 정보, 위험, 후속 행동과 상담문을 반환합니다.
5. 브라우저가 결과를 표시하고 기관 추천 규칙을 적용합니다.

## 사용 데이터

- 행정안전부 「지방자치단체 외국인주민 현황」, KOSIS, 2022~2024
- 개발자가 제작한 가상 급여명세서·임대차계약서·공과금 고지서
- 대표 문서 3종의 구조화 분석 JSON 및 4개 언어 결과
- 공식 사이트를 출처로 정리한 대구 지원기관 10곳
- 피싱/정상 문장 각 100건의 별도 분류 실험 데이터

## 개인정보 및 한계

- 프로토타입은 업로드 파일을 자체 DB에 저장하지 않습니다.
- 파일은 분석을 위해 외부 AI API로 전송되므로 실제 개인정보가 포함된 문서를 데모에 사용하지 않는 것을 권장합니다.
- 기관 추천은 실시간 위치나 거리순이 아니라 선택한 구·군과 문서 유형에 따른 규칙입니다.
- 금융·법률 판단을 확정하지 않으며, 중요한 계약이나 납부 내용은 원문과 담당 기관에서 다시 확인해야 합니다.

## 데모

공개 데모는 Streamlit Community Cloud에서 이 저장소의 `streamlit_app.py`를 선택해 배포합니다. 기존 ChatGPT Sites 주소는 로그인 없이 열리지 않을 수 있어 제출용 공개 링크로 사용하지 않습니다.
