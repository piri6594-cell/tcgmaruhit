# TCGMARUHIT 배포 가이드

## 서버 구조

```
사용자 브라우저
    ↓
tcgmaruhit.com (Cloudflare DNS)
    ↓
Railway (Flask 서버)
    ├── 박스·히트카드·정산·도감 (서버 내부, 비용 0)
    └── 카드 진단
        ├── 1순위: 로컬 Qwen (주인님 PC, 0원)
        └── 2순위: Gemini Flash-Lite API (회당 0.13센트)
```

## 데이터베이스와 결제 상태

컬렉션과 구독 상태는 SQLAlchemy Core의 schema version 1 테이블에 저장한다. Railway에서는 반드시 `TCG_DATABASE_URL`을 PostgreSQL URL로 설정한다. production mode에서 이 변수가 없으면 정적 API와 health만 유지되고 컬렉션·구독 변경 API는 `503 TCG_DATABASE_URL_REQUIRED`로 fail-closed 한다.

`payment_intents`는 서버가 생성한 random `orderId`와 device owner·금액·만료시각을 저장한다. activate와 Toss webhook은 DB intent를 확인한 뒤 네트워크 검증을 수행하고, 검증 결과와 premium 갱신만 짧은 transaction에서 처리한다. `paymentKey`와 `orderId`는 각각 unique라 webhook 재전송은 같은 구독 결과를 반환한다.

기존 JSON은 원본을 덮어쓰지 않고 다음처럼 확인·적용한다.

```powershell
python scripts/migrate_json_to_db.py --dry-run --database-url $env:TCG_DATABASE_URL
python scripts/migrate_json_to_db.py --apply --database-url $env:TCG_DATABASE_URL
python scripts/migrate_json_to_db.py --verify --database-url $env:TCG_DATABASE_URL
python scripts/migrate_json_to_db.py --export-rollback --output-dir .\rollback-export --database-url $env:TCG_DATABASE_URL
```

PostgreSQL pool은 `pool_size=1`, `max_overflow=1`, `pool_timeout=5`, `pool_pre_ping=True`로 제한하고 SQLite에는 PostgreSQL pool 옵션을 적용하지 않는다.

## 1단계: GitHub에 코드 올리기 (내가 함)

```bash
cd C:\Hermes\work\tcg_service_v04_20260712
git init
git add .
git commit -m "TCGMARUHIT v0.4 — 배포 준비"
git branch -M main
```

GitHub에 새 저장소를 만들고 올린다.

## 2단계: Railway 배포 (주인님이 함)

1. https://railway.app 접속 → 가입 (GitHub 계정으로)
2. **New Project** → **Deploy from GitHub repo**
3. 방금 올린 저장소 선택
4. Railway가 자동으로:
   - `requirements.txt` 설치
   - `Procfile` 읽고 `gunicorn` 실행
   - `https://xxx.up.railway.app` 주소 발급
5. **Variables** 탭에서 환경변수 설정:
   - `GEMINI_API_KEY` = (Google AI Studio에서 발급)
   - `PORT` = (Railway가 자동 설정)

## 3단계: Gemini API 키 발급 (무료)

1. https://aistudio.google.com/apikey 접속
2. **Create API Key** 클릭
3. 발급된 키를 Railway Variables에 입력

Gemini 3.1 Flash-Lite 무료 등급:
- 분당 30회, 일일 1500회 무료
- 초과 시 100만 토큰당 $0.25

## 4단계: 도메인 연결 (주인님이 함)

### 가비아 DNS 설정

1. 가비아 → 도메인 관리 → tcgmaruhit.com
2. DNS 설정 → **레코드 추가**
3. Railway에서 발급받은 주소를 CNAME으로 연결

```
형식: CNAME
호스트: @ (또는 www)
값: xxx.up.railway.app (Railway에서 제공)
```

또는 Railway에서 **Custom Domain**을 직접 추가하고 가비아 DNS를 Railway 네임서버로 변경.

### Railway에서 Custom Domain

1. Railway → Settings → **Networking**
2. **Generate Domain** → Railway가 `xxx.up.railway.app` 발급
3. **Custom Domain** 추가 → `tcgmaruhit.com`
4. Railway가 DNS 레코드를 안내 → 가비아에 입력

## 5단계: HTTPS (자동)

Railway는 자동으로 Let's Encrypt SSL 인증서를 발급한다.
별도 작업 없음.

## 월 비용 정리

| 항목 | 비용 |
|------|------|
| Railway Hobby 플랜 | $5/월 (약 7,000원) |
| 도메인 tcgmaruhit.com | 연 22,000원 (월 약 1,800원) |
| Gemini API (일 1500회 무료) | $0 ~ 소액 |
| **총 월 비용** | **약 9,000원** |

## 주인님이 할 것 (순서)

1. ⬜ GitHub 계정 확인/생성
2. ⬜ Railway 가입 (https://railway.app)
3. ⬜ Google AI Studio에서 Gemini API 키 발급 (https://aistudio.google.com/apikey)
4. ⬜ 이 가이드대로 진행하다가 막히면 나한테 물어보기

## 내가 할 것

1. ✅ 배포용 코드 정리 (완료)
2. ✅ requirements.txt / Procfile / .gitignore (완료)
3. ✅ Gemini API 백엔드 구현 (완료)
4. ⬜ GitHub 저장소 생성 + 코드 푸시
5. ⬜ Railway 배포 후 도메인 연결 지원
