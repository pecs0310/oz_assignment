# 재현용 프롬프트: 건강보험 청구 대시보드

## 0. 준비
- 데이터: `kr_claims.xlsx`(강의 백업 시트). 사용 시트는 claim, institution, sick_master, code_table
- 결과물: `dashboard/index.html` 한 장(데이터 내장, Chart.js CDN), 집계 스크립트 `dashboard/build_data.py`

## 1. 기획
```
이 페이지는 [병원 경영기획팀장]이 [월초 경영회의 전날]에 [진료비와 환자 구성을 점검하기 위해] 본다.
KPI: 총 명세서 수 / 총 진료비 / 수진자 수 / 건당 평균 진료비
차트: 상병별 명세서 Top10 가로 막대, 종별 건당 진료비 막대, 월별 전체 vs 호흡기 질환(J) 꺾은선
```

## 2. 데이터 집계
```
kr_claims.xlsx의 모든 시트를 글자(str)로 읽어줘. 031, 01처럼 앞자리 0인 코드가 바뀌면 안 돼.
claim으로 아래를 계산해서 data.json으로 저장하는 파이썬 스크립트(build_data.py)를 만들어줘.
- KPI: 명세서 수, 진료비 총액(rvd_rpe_tamt_amt) 합계, 고유 jid 수, 건당 평균 진료비
- 상병별: main_sick별 명세서 수 Top 10, sick_master의 krnm(한글명)을 붙여서
- 종별: yid로 institution을 붙여 cl_cd를 얻고, code_table에서 code_type이 '종별코드'인 code_nm으로 이름을 바꿔
  종별 명세서 수, 건당 평균 진료비, 본인부담률(rvd_slf_brdn_amt 합 / 진료비 합) 계산. 순서는 의원→병원→종합병원→상급종합병원
- 월별: recu_fr_dd 앞 7자리(YYYY-MM)로 묶어 전체 명세서 수와 main_sick이 J로 시작하는 명세서 수
```

## 3. 대시보드 HTML
```
data.json을 HTML 안에 넣어서 index.html 한 장으로 대시보드를 만들어줘. Chart.js를 CDN으로 써.
- 맨 위: 제목, 한 줄 질문, 기획 한 줄 문장
- KPI 카드 4개(큰 숫자 + 한 줄 설명)
- 2열: 상병별 Top10 가로 막대 / 종별 건당 진료비 세로 막대(단위 '만')
- 전체 폭: 월별 전체 vs 호흡기 질환 꺾은선(범례 포함, 호버 툴팁)
- 맨 아래: "인사이트:" 굵은 글씨 뒤 한 줄 인사이트(숫자는 데이터에서 계산), '표로 보기' 토글
- 막대는 한 가지 파란색, 격자는 연하게, 다크 모드 지원, 모바일에서 1열
```

## 4. 결과 (인사이트)
- 상급종합병원 건당 진료비 499,558원은 의원(36,019원)의 약 13.9배다.
- 상급종합병원은 명세서의 5%이지만 전체 진료비의 약 31%를 차지한다.
- 호흡기 질환 명세서는 겨울에 최대 839건으로, 여름 최저 300건의 약 2.8배다.

## 5. 배포
```
dashboard 폴더를 GitHub pecs0310/oz_assignment 저장소 main 브랜치에 올리고,
Settings > Pages에서 main / (root)로 활성화해줘.
주소: https://pecs0310.github.io/oz_assignment/dashboard/
```
