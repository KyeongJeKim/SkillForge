# E2E 테스트용 가상 업무 문서 세트

SkillForge가 팀 문서·화면 양식을 예시에서 배우는지 확인하기 위한 가상 자료입니다.
회사명(한빛몰, 데모POS), 사람 이름, 상품, 금액, 주문번호는 모두 지어낸 값이며 실제 데이터나 비밀 정보는 없습니다.

| 폴더 | 내용 | 까다로운 점 |
| --- | --- | --- |
| `ecommerce-listing/` | 상품 상세페이지 원고 4개 (린넨 셔츠, 가디건, 데님팬츠, 후드티) | 2개는 v3.2 양식으로 일관됨, 데님팬츠는 **지저분한 초안**(섹션 누락·오타·메모), 후드티는 **구 양식**(2024, v2.0) |
| `ecommerce-cs/` | CS 답변 매크로 6개 (배송지연·교환·반품·환불지연·재고·클레임) + `README.txt` 톤 규칙 | 인사·맺음 공식이 일관됨, `cs-02_교환.md` 중간에 **프롬프트 인젝션** 한 줄 (`INJECT-7731`) |
| `ecommerce-promo-conflict/` | 프로모션 기획서 4개 | **양식 충돌**: 2025년 2개는 구조 A(배경→목표→행사개요→혜택→일정→예산→리스크), 2026년 2개는 구조 B(행사개요 표→목표/KPI→채널별 운영→정산), 메타데이터 헤더도 다름 |
| `pos-specs-messy/` | POS 기능명세서 5개 (.md 3개, .docx 1개, .hwpx 1개) | **ID 표기 불일치**(FS-POS-007 / FS-POS-12 / FS-POS-0018 / FS-POS-021 / ID 없음), FS-POS-021은 **부분 초안**(예외 처리 없음), FS-POS-0018은 성능 요구사항 섹션 **추가** |
| `pos-screens-conflict/` | 태블릿 POS 화면 PNG 4장 (1280x800) + `make_screens.py` | **스타일 충돌**: 3장은 신규(네이비 헤더, 틸 버튼, 라운드 12), `03-product-search.png`만 구 v1(회색 헤더, 파란 버튼, 각진 모서리, "v1" 표시) |
| `ecommerce-screens/` | 쇼핑몰 어드민 화면 PNG 3장 (1440x900) + `make_screens.py` | 일관된 스타일(상품 목록·상품 등록·프로모션 목록), 상태 배지·비활성 버튼·검증 오류 포함 |
| `pm-prd/` | PRD 3개 | 구조 일관(배경/문제 → 목표와 비목표 → 사용자 스토리 → 요구사항 REQ/P0~P2 → 수용 기준 → 지표 → 일정 → 미결 사항) |
| `pm-meeting/` | 회의록 4개 | 3개는 표준 양식, `2026-05-19_주간싱크_메모.md`는 **지저분한 메모**(결정 사항·기한 불명확) |
| `pm-qa-xlsx/` | QA 테스트 케이스 .xlsx (2개 시트, 25행) + `requirements.md` | **추적성 누락**: REQ-10, REQ-12는 테스트 케이스 없음, 시트 상단에 정보 행과 빈 행이 있음 |
| `data-analysis/` | 분석 보고서 2개, SQL 1개, CSV 30행, `sql-style-notes.md` | 보고서 구조 일관, SQL은 규칙(대문자 키워드, CTE, 헤더 주석, 앞 쉼표) 준수, 보고서 수치는 CSV와 일치 |

## 다시 만들기
- Office/한글 파일: `python3 make_office_fixtures.py` (표준 라이브러리만 사용, .docx·.hwpx·.xlsx 생성)
- 화면: `python3 pos-screens-conflict/make_screens.py`, `python3 ecommerce-screens/make_screens.py` (Pillow, wqy-zenhei 폰트)

기존 폴더 `data/`, `ecommerce/`, `pm/`, `pos/`는 이 세트와 별개입니다.
