# ETF 대시보드 (2주 자동 갱신)

미국·한국 ETF TOP 10 시세를 2주(격주)마다 자동으로 가져와 정적 HTML 대시보드를 갱신합니다.
데이터 소스는 [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance 기반, **API 키 불필요, 무료**)입니다.

## 구성

```
etf-dashboard/
├── scripts/fetch_and_render.py   # 시세 조회 + HTML 생성
├── data/history.json             # 매 실행마다 쌓이는 시세 히스토리 (자동 생성)
├── index.html                    # 최종 대시보드 (자동 생성)
├── requirements.txt
└── .github/workflows/update-dashboard.yml   # 2주 간격 자동 실행 설정
```

## 처음 설정하는 법

1. **GitHub에 새 저장소(repository)를 만들고, 이 폴더 전체를 업로드/푸시**하세요.
   ```bash
   cd etf-dashboard
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

2. **GitHub Pages 켜기** (대시보드를 웹에서 바로 보고 싶다면):
   - 저장소 → Settings → Pages
   - Source: `Deploy from a branch` → Branch: `main` / `/ (root)` 선택 → Save
   - 몇 분 뒤 `https://<your-username>.github.io/<repo-name>/`에서 대시보드 확인 가능

3. **끝!** `.github/workflows/update-dashboard.yml`이 매달 1일·15일(약 2주 간격)에
   자동으로 실행되어 `index.html`과 `data/history.json`을 갱신하고 커밋합니다.

## 지금 바로 한 번 실행해보고 싶다면

저장소 → **Actions** 탭 → `Update ETF Dashboard` 워크플로 → **Run workflow** 버튼을 누르면
스케줄을 기다리지 않고 바로 1회 실행됩니다.

## 로컬에서 직접 실행하기

```bash
pip install -r requirements.txt
python scripts/fetch_and_render.py
# index.html이 생성/갱신됩니다. 브라우저로 열어 확인하세요.
```

## 종목 리스트 수정하기

`scripts/fetch_and_render.py` 상단의 `US_ETFS`, `KR_ETFS` 딕셔너리를 편집하면 됩니다.
한국 종목은 KRX 코드 뒤에 `.KS`를 붙인 형식이에요 (예: 삼성전자 `005930.KS`).

## 주기 바꾸기

`.github/workflows/update-dashboard.yml`의 `cron` 값을 수정하세요.
예: 매주 월요일 00:00 UTC → `"0 0 * * 1"`. cron 표현식은 [crontab.guru](https://crontab.guru)에서 쉽게 만들 수 있어요.

## 참고

- Yahoo Finance 기반 데이터라 무료지만, 공식 API가 아니라서 드물게 일시적으로 응답이 안 될 수 있어요.
  스크립트는 종목 하나가 실패해도 나머지는 계속 진행하도록 만들어져 있습니다.
- Claude 토큰은 이 자동화가 실행되는 동안 전혀 사용되지 않아요 — 스크립트가 Yahoo Finance를 직접 호출합니다.
