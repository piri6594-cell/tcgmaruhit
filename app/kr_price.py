
"""
한국 TCG 시세 추정기
- TCGPlayer USD 기준가 → 원화 환산
- 한국 마켓 프리미엄: 등급/레어도별 가중치
- 번개장터/카드킹덤 검색 링크 생성
"""

# 한국 프리미엄 배율 (레어도별)
KR_PREMIUM = {
    "Special Illustration Rare": 1.5,
    "Hyper Rare": 1.4,
    "Illustration Rare": 1.35,
    "Ultra Rare": 1.3,
    "Shiny Rare": 1.3,
    "Double Rare": 1.2,
    "Radiant Rare": 1.2,
    "Amazing Rare": 1.25,
    "ACE SPEC Rare": 1.2,
    "Rare": 1.15,
    "Uncommon": 1.05,
    "Common": 1.0,
    "Promo": 1.3,
}

USD_TO_KRW = 1380  # 대략적 환율

def estimate_krw(usd_price, rarity):
    """USD 가격 → 한국 추정가 (원)"""
    if not usd_price:
        return None
    premium = KR_PREMIUM.get(rarity, 1.2)
    krw = usd_price * USD_TO_KRW * premium
    return {
        "krw_estimated": round(krw),
        "krw_range_low": round(krw * 0.7),
        "krw_range_high": round(krw * 1.3),
        "usd_base": usd_price,
        "premium": premium,
        "exchange_rate": USD_TO_KRW,
    }

def search_link(card_name_kr):
    """번개장터 검색 링크"""
    import urllib.parse
    q = urllib.parse.quote(f"포켓몬카드 {card_name_kr}")
    return f"https://bunjang.co.kr/search/products?q={q}"

if __name__ == "__main__":
    print("한국 시세 추정기 로드 완료")
