"""
TCG 통합 서비스 v0.4
박스 탐색 + 히트카드 + 진단 + 정산 + 도감
"""
import os, json, math, cv2, numpy as np, base64, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ═════════════════════════════════════════════════════════════
# 박스 데이터
# ═════════════════════════════════════════════════════════════

BOXES = [
    {"id":"blackbolt","name":"블랙볼트","code":"SV11B","lang":"kr","release":"2026-04","packs":30,"cpp":5,"price_kr":135000,"retail_price":40000,"price_jp":235000,"sold_out":True,"img":"/box-img/blackbolt.png","desc":"티탱크 ex, 두빅굴, 무쿠무쿠",
     "hits":[{"n":"티탱크 ex SR","r":"SR","p":45000,"rate":"1/30"},{"n":"두빅굴 SAR","r":"SAR","p":80000,"rate":"1/60"},{"n":"무쿠무쿠 SAR","r":"SAR","p":60000,"rate":"1/60"},{"n":"티탱크 ex AR","r":"AR","p":12000,"rate":"1/10"}]},
    {"id":"whiteflare","name":"화이트플레어","code":"SV11A","lang":"kr","release":"2026-04","packs":30,"cpp":5,"price_kr":110000,"retail_price":40000,"price_jp":200000,"sold_out":True,"img":"/box-img/whiteflare.png","desc":"레시라무 ex, 가디안, 수댕이",
     "hits":[{"n":"레시라무 ex SR","r":"SR","p":120000,"rate":"1/30"},{"n":"가디안 SAR","r":"SAR","p":90000,"rate":"1/60"},{"n":"수댕이 SAR","r":"SAR","p":25000,"rate":"1/60"},{"n":"레시라무 ex AR","r":"AR","p":15000,"rate":"1/10"}]},
    {"id":"infernox","name":"인페르노X","code":"SV10a","lang":"kr","release":"2026-03","packs":30,"cpp":5,"price_kr":63000,"retail_price":30000,"price_jp":120000,"sold_out":True,"img":"/box-img/infernox.png","desc":"리자몽 ex, 빛나, 푸크린",
     "hits":[{"n":"리자몽 ex SR","r":"SR","p":35000,"rate":"1/30"},{"n":"리자몽 ex SAR","r":"SAR","p":120000,"rate":"1/90"},{"n":"빛나 SAR","r":"SAR","p":18000,"rate":"1/60"},{"n":"푸크린 AR","r":"AR","p":3000,"rate":"1/10"}]},
    {"id":"nihilzero","name":"니힐제로","code":"SV12","lang":"kr","release":"2026-06","packs":30,"cpp":5,"price_kr":35000,"retail_price":30000,"price_jp":80000,"sold_out":True,"img":"/box-img/nihilzero.png","desc":"니힐제로, 신규 메카닉",
     "hits":[{"n":"니힐제로 SR","r":"SR","p":15000,"rate":"1/30"},{"n":"니힐제로 SAR","r":"SAR","p":40000,"rate":"1/60"}]},
    {"id":"abyss","name":"어비스아이","code":"SV10b","lang":"kr","release":"2026-03","packs":30,"cpp":5,"price_kr":48000,"retail_price":45000,"price_jp":95000,"sold_out":True,"img":"/box-img/abyss.png","desc":"메가다크라이 ex, 메가제라오라 ex",
     "hits":[{"n":"메가다크라이 ex SR","r":"SR","p":50000,"rate":"1/30"},{"n":"메가제라오라 ex SAR","r":"SAR","p":35000,"rate":"1/60"},{"n":"이슬의 기력 SAR","r":"SAR","p":12000,"rate":"1/60"},{"n":"무쿠무쿠 SAR","r":"SAR","p":40000,"rate":"1/60"}]},
    {"id":"ninjaspinner","name":"닌자스피너","code":"SV9a","lang":"kr","release":"2026-02","packs":30,"cpp":5,"price_kr":40000,"retail_price":30000,"price_jp":75000,"sold_out":True,"img":"/box-img/ninjaspinner.png","desc":"한카리아스 ex, 루카리오",
     "hits":[{"n":"한카리아스 ex SR","r":"SR","p":25000,"rate":"1/30"},{"n":"루카리오 SAR","r":"SAR","p":18000,"rate":"1/60"}]},
    {"id":"151","name":"151","code":"SV3a","lang":"kr","release":"2025-09","packs":30,"cpp":5,"price_kr":50000,"retail_price":50000,"price_jp":90000,"sold_out":True,"img":"/box-img/151.png","desc":"관동 151종, 뮤츠 ex, 나옹",
     "hits":[{"n":"뮤츠 ex SR","r":"SR","p":35000,"rate":"1/30"},{"n":"뮤츠 ex SAR","r":"SAR","p":80000,"rate":"1/90"},{"n":"나옹 SAR","r":"SAR","p":50000,"rate":"1/90"},{"n":"이브이 master","r":"master","p":200000,"rate":"1/300"}]},
    {"id":"vstar","name":"VSTAR 유니버스","code":"S12a","lang":"kr","release":"2025-01","packs":30,"cpp":5,"price_kr":35000,"retail_price":50000,"price_jp":70000,"sold_out":True,"img":"/box-img/vstar.png","desc":"아르세우스 VSTAR, 리피아 VSTAR",
     "hits":[{"n":"아르세우스 VSTAR SR","r":"SR","p":18000,"rate":"1/30"},{"n":"리피아 VSTAR SR","r":"SR","p":12000,"rate":"1/30"},{"n":"디안시 SR","r":"SR","p":2500,"rate":"1/30"}]},
    {"id":"megadream","name":"MEGA 드림 ex","code":"SV9b","lang":"kr","release":"2026-02","packs":30,"cpp":5,"price_kr":15000,"retail_price":30000,"price_jp":35000,"sold_out":False,"img":"/box-img/megadream.png","desc":"메가리자몽X ex, 피카츄 ex",
     "hits":[{"n":"메가리자몽X ex SR","r":"SR","p":30000,"rate":"1/30"},{"n":"피카츄 ex SR","r":"SR","p":95000,"rate":"1/30"},{"n":"피카츄 ex SAR","r":"SAR","p":145000,"rate":"1/90"}]},
    {"id":"rocket","name":"로켓단의 영광","code":"SV8a","lang":"kr","release":"2026-01","packs":30,"cpp":5,"price_kr":46000,"retail_price":30000,"price_jp":85000,"sold_out":True,"img":"/box-img/rocket.png","desc":"악비라르 ex, 블래키 VMAX",
     "hits":[{"n":"악비라르 ex SR","r":"SR","p":22000,"rate":"1/30"},{"n":"블래키 VMAX R","r":"R","p":730000,"rate":"1/200"}]},
    {"id":"terastal","name":"테라스탈 페스타 ex","code":"SV8","lang":"kr","release":"2025-12","packs":30,"cpp":5,"price_kr":50000,"retail_price":50000,"price_jp":60000,"sold_out":True,"img":"/box-img/terastal.png","desc":"님피아 ex, 테라스탈",
     "hits":[{"n":"님피아 ex SR","r":"SR","p":75000,"rate":"1/30"}]},
    {"id":"ebreaker","name":"초전브레이커","code":"SV10","lang":"kr","release":"2026-03","packs":30,"cpp":5,"price_kr":44000,"retail_price":30000,"price_jp":85000,"sold_out":True,"img":"/box-img/ebreaker.png","desc":"피카츄 ex, 티탱크 ex",
     "hits":[{"n":"피카츄 ex SR","r":"SR","p":145000,"rate":"1/30"},{"n":"피카츄 ex SAR","r":"SAR","p":200000,"rate":"1/90"}]},
]

RECENT_TRADES = [
    {"name":"피카츄 ex SAR","box":"초전브레이커","lang":"KR","grade":"PSA10","price":200000,"source":"번개장터","date":"2026-07-12"},
    {"name":"블래키 VMAX R","box":"로켓단의 영광","lang":"KR","grade":"Raw","price":680000,"source":"크림","date":"2026-07-11"},
    {"name":"레시라무 ex SR","box":"화이트플레어","lang":"KR","grade":"PSA9","price":95000,"source":"스니덩","date":"2026-07-10"},
    {"name":"뮤츠 ex SAR","box":"151","lang":"KR","grade":"PSA10","price":75000,"source":"번개장터","date":"2026-07-10"},
    {"name":"티탱크 ex SR","box":"블랙볼트","lang":"KR","grade":"Raw","price":38000,"source":"BREAK","date":"2026-07-09"},
    {"name":"메가다크라이 ex SR","box":"어비스아이","lang":"KR","grade":"PSA10","price":48000,"source":"cardchange","date":"2026-07-08"},
    {"name":"리자몽 ex SAR","box":"인페르노X","lang":"KR","grade":"PSA9","price":110000,"source":"번개장터","date":"2026-07-08"},
    {"name":"가디안 SAR","box":"화이트플레어","lang":"KR","grade":"Raw","price":80000,"source":"크림","date":"2026-07-07"},
]

def get_boxes(): return BOXES
def get_box(bid): return next((b for b in BOXES if b["id"] == bid), None)

def get_all_hits():
    out = []
    for b in BOXES:
        for h in b.get("hits", []):
            out.append({"name": h["n"], "rarity": h["r"], "est_price": h["p"], "pull_rate": h["rate"],
                        "box_id": b["id"], "box_name": b["name"], "code": b["code"], "box_img": b.get("img","")})
    return out

def box_ev(box):
    ev = 0
    for h in box.get("hits", []):
        try:
            denom = int(h["rate"].split("/")[1])
            ev += h["p"] / denom
        except: pass
    total = sum(h["p"] for h in box.get("hits", []))
    return {"ev_per_box": int(ev), "total_hit_value": total,
            "ev_ratio": round(ev / box["price_kr"] * 100, 1) if box["price_kr"] > 0 else 0}

# ═════════════════════════════════════════════════════════════
# 정산
# ═════════════════════════════════════════════════════════════

CHANNELS = [
    {"name":"번개장터","pct":3.5,"fixed":0,"pay_pct":2.9,"pay_fixed":300,"ship":3000,"ins":500},
    {"name":"크림(KREAM)","pct":0,"fixed":3000,"pay_pct":0,"pay_fixed":0,"ship":0,"ins":0},
    {"name":"eBay(통합)","pct":13.25,"fixed":0,"pay_pct":2.95,"pay_fixed":0,"ship":0,"ins":0},
    {"name":"스니덩","pct":10,"fixed":0,"pay_pct":0,"pay_fixed":0,"ship":0,"ins":0},
    {"name":"BREAK","pct":3,"fixed":0,"pay_pct":0,"pay_fixed":0,"ship":0,"ins":0},
    {"name":"직거래","pct":0,"fixed":0,"pay_pct":0,"pay_fixed":0,"ship":0,"ins":0},
]

def calc_settle(sp, cost):
    out = []
    for ch in CHANNELS:
        fee = int(sp * ch["pct"] / 100) + ch["fixed"] + int(sp * ch["pay_pct"] / 100) + ch["pay_fixed"] + ch["ship"] + ch["ins"]
        net = sp - fee
        profit = net - cost
        roi = round(profit / cost * 100, 1) if cost > 0 else 0
        out.append({"channel": ch["name"], "sale_price": sp, "fee_total": fee, "net_income": net, "cost": cost, "profit": profit, "roi": roi})
    return out

# ═════════════════════════════════════════════════════════════
# 카드 진단
# ═════════════════════════════════════════════════════════════

class CardGrader:
    CW, CH = 600, 840
    QURL = "http://127.0.0.1:18087/v1"
    MODEL = "Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-Q6_K_P.gguf"
    PSAC = {10: 55.0, 9: 60.0, 8: 65.0, 7: 70.0}
    GMAP = {'mint': 10, 'near mint': 9, 'lightly played': 7, 'moderately played': 5, 'heavily played': 3, 'damaged': 1}

    def __init__(self):
        # 1순위: 로컬 Qwen, 2순위: Gemini API
        self.qwen = False
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")
        self.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.backend = "none"
        try:
            if requests.get(f"{self.QURL}/models", timeout=3).status_code == 200:
                self.qwen = True
                self.backend = "qwen"
        except:
            pass
        if not self.qwen and self.gemini_key:
            self.backend = "gemini"

    @property
    def active_model(self):
        if self.backend == "qwen":
            return self.MODEL
        if self.backend == "gemini":
            return self.gemini_model
        return None

    def process(self, path):
        img = cv2.imread(path)
        if img is None: raise ValueError("이미지 불가")
        h, w = img.shape[:2]
        if max(h, w) > 1200:
            s = 1200 / max(h, w); img = cv2.resize(img, (int(w * s), int(h * s)))
        # 이미지 품질 체크
        quality = self._check_quality(img)
        
        pts = self._detect(img)
        if pts is not None:
            card = self._correct(img, pts)
            card_detected = True
        else:
            card = cv2.resize(img, (self.CW, self.CH))
            card_detected = False
        cen = self._centering(card)
        ann = self._annotate(card, cen)
        crops = self._crop(card)
        if self.backend == "qwen":
            corners, surface = self._qwen_all(crops)
        elif self.backend == "gemini":
            corners, surface = self._gemini_all(crops)
        else:
            corners = {k: "AI 분석 미가동 (API 키 필요)" for k in ['top_left','top_right','bottom_left','bottom_right']}
            surface = "AI 분석 미가동 (API 키 필요)"
        ov, notes = self._combine(cen, corners, surface)
        
        # 카드 식별 (Gemini/Qwen으로 카드 텍스트 읽기)
        card_name = ""
        card_identified = False
        if self.backend in ("qwen", "gemini"):
            card_name = self._identify_card(card)
            if card_name:
                card_identified = True
        
        return {"centering": asdict(cen), "qwen_corners": corners, "qwen_surface": surface,
                "overall_grade_range": ov[0], "overall_min_score": ov[1], "overall_confidence": ov[2],
                "notes": notes, "annotated_b64": self._b64(ann), "corrected_b64": self._b64(card),
                "backend": self.backend,
                "card_detected": card_detected,
                "card_name": card_name,
                "card_identified": card_identified,
                "quality": quality,
                "disclaimer": "참고용이며 실제 PSA/BGS/CGC 결과와 다를 수 있습니다."}

    def _check_quality(self, img):
        """이미지 품질 체크 — 빛 반사, 해상도, 흐림"""
        h, w = int(img.shape[0]), int(img.shape[1])
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 빛 반사: 밝은 픽셀 비율
        bright_ratio = float((gray > 240).sum()) / float(h * w)
        # 흐림 정도: 라플라시안 분산
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        # 해상도 충분?
        resolution_ok = bool(min(h, w) >= 400)
        # 빛 반사 심함?
        glare_warning = bool(bright_ratio > 0.12)
        # 흐림 경고
        blur_warning = bool(blur_score < 50)
        quality_ok = bool(resolution_ok and not glare_warning and not blur_warning)
        return {
            "width": w, "height": h,
            "resolution_ok": resolution_ok,
            "bright_ratio": round(bright_ratio, 3),
            "glare_warning": glare_warning,
            "blur_score": round(blur_score, 1),
            "blur_warning": blur_warning,
            "quality_ok": quality_ok,
        }

    def _identify_card(self, card_img):
        """카드 텍스트를 읽어 포켓몬 이름 식별"""
        b64 = self._b64(card_img)
        prompt = ("트레이딩 카드 전체 사진이다. 이 카드의 정보를 읽어라.\n"
                  "1. 포켓몬 이름 (한국어)\n"
                  "2. HP 숫자\n"
                  "3. 카드에 적힌 번호 (예: 054/088)\n"
                  "형식:\n이름:(이름)\nHP:(숫자)\n번호:(번호)\n"
                  "모르면 '불가'라고 써라.")
        try:
            if self.backend == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
                payload = {
                    "contents": [{"parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
                    ]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100}
                }
                r = requests.post(url, json=payload, timeout=60)
                data = r.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            else:
                r = requests.post(f"{self.QURL}/chat/completions", json={
                    "model": self.MODEL,
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": "<|think_off|>\n" + prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}],
                    "max_tokens": 100, "temperature": 0.1
                }, timeout=60)
                text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            # 이름 추출
            for line in text.strip().split("\n"):
                if "이름:" in line or "이름 :" in line:
                    name = line.split(":")[-1].strip()
                    if name and name != "불가":
                        return name
            return ""
        except:
            return ""

    def _detect(self, img):
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        b = cv2.GaussianBlur(g, (5,5), 0)
        for m in ['otsu','canny']:
            binary = cv2.threshold(b,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1] if m=='otsu' else cv2.Canny(b,30,150)
            cnts,_ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
                if cv2.contourArea(c) < 5000: continue
                peri = cv2.arcLength(c, True)
                ap = cv2.approxPolyDP(c, 0.02*peri, True)
                if len(ap) == 4: return self._order(ap.reshape(4,2).astype(np.float32))
        return None

    def _order(self, pts):
        r = np.zeros((4,2), dtype="float32")
        s = pts.sum(axis=1); r[0] = pts[np.argmin(s)]; r[2] = pts[np.argmax(s)]
        d = np.diff(pts, axis=1); r[1] = pts[np.argmin(d)]; r[3] = pts[np.argmax(d)]
        return r

    def _correct(self, img, pts):
        dst = np.array([[0,0],[self.CW-1,0],[self.CW-1,self.CH-1],[0,self.CH-1]], dtype="float32")
        M = cv2.getPerspectiveTransform(pts, dst)
        return cv2.warpPerspective(img, M, (self.CW, self.CH))

    def _centering(self, card):
        g = cv2.cvtColor(card, cv2.COLOR_BGR2GRAY)
        h, w = g.shape
        hg = np.abs(np.diff(g[int(h*.35):int(h*.65),:].mean(axis=0).astype(np.float64)))
        sl, sr = int(w*.15), int(w*.85)
        lb = int(np.argmax(hg[:sl]))+1
        rb = w-(sr+int(np.argmax(hg[sr:]))+1)
        ht = lb+rb; hpl = (lb/ht*100) if ht > 0 else 50; hpr = 100-hpl; hw = max(hpl,hpr)
        vg = np.abs(np.diff(g[:,int(w*.35):int(w*.65)].mean(axis=1).astype(np.float64)))
        st, sb = int(h*.15), int(h*.85)
        tb = int(np.argmax(vg[:st]))+1
        bb = h-(sb+int(np.argmax(vg[sb:]))+1)
        vt = tb+bb; vpt = (tb/vt*100) if vt > 0 else 50; vpb = 100-vpt; vw = max(vpt,vpb)
        worse = max(hw,vw); grade = 6
        for gr, th in sorted(self.PSAC.items(), reverse=True):
            if worse <= th: grade = gr; break
        @dataclass
        class C:
            left_px:int; right_px:int; top_px:int; bottom_px:int
            horizontal_ratio:str; vertical_ratio:str
            horizontal_worst:float; vertical_worst:float
            centering_grade:int; psa_10_ok:bool; psa_9_ok:bool
        return C(lb,rb,tb,bb,f"{hpl:.1f} / {hpr:.1f}",f"{vpt:.1f} / {vpb:.1f}",round(hw,1),round(vw,1),grade,hw<=55 and vw<=55,hw<=60 and vw<=60)

    def _annotate(self, card, cen):
        a = card.copy(); h, w = a.shape[:2]
        c = (0,200,0) if cen.psa_10_ok else (0,0,200)
        cv2.line(a,(cen.left_px,0),(cen.left_px,h),c,2)
        cv2.line(a,(w-cen.right_px,0),(w-cen.right_px,h),c,2)
        cv2.line(a,(0,cen.top_px),(w,cen.top_px),c,2)
        cv2.line(a,(0,h-cen.bottom_px),(w,h-cen.bottom_px),c,2)
        f = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(a,f"H:{cen.horizontal_ratio}",(10,h-15),f,0.55,(255,255,255),2)
        cv2.putText(a,f"V:{cen.vertical_ratio}",(10,25),f,0.55,(255,255,255),2)
        cv2.putText(a,f"PSA {cen.centering_grade}",(w-200,h-15),f,0.55,(255,255,255),2)
        return a

    def _crop(self, card):
        h, w = card.shape[:2]; cs = 130
        return {'top_left':card[0:cs,0:cs],'top_right':card[0:cs,w-cs:w],
                'bottom_left':card[h-cs:h,0:cs],'bottom_right':card[h-cs:h,w-cs:w],
                'surface':card[int(h*.35):int(h*.55),int(w*.25):int(w*.75)]}

    def _qwen_all(self, crops):
        corners = {}; surface = ""
        with ThreadPoolExecutor(max_workers=5) as pool:
            futs = {pool.submit(self._qwen_one,n,self._b64(img)):n for n,img in crops.items()}
            for f in as_completed(futs):
                n = futs[f]; r = f.result()
                if n == 'surface': surface = r
                else: corners[n] = r
        return {k:corners.get(k,"") for k in ['top_left','top_right','bottom_left','bottom_right']}, surface

    def _qwen_one(self, name, b64):
        if name == 'surface':
            p = "<|think_off|>\n트레이딩 카드 표면 중앙 확대. 객관적 관찰.\n1.스크래치 2.인쇄결함 3.코팅벗겨짐 4.종합(Mint/Near Mint/Lightly Played/Damaged)\n형식:\n스크래치:(관찰)\n인쇄:(관찰)\n코팅:(관찰)\n등급:(등급)"
        else:
            p = "<|think_off|>\n트레이딩 카드 모서리 확대. 객관적 관찰.\n1.모서리(뾰족/뭉툭) 2.흰점/백화 3.눌림/찌그러짐 4.종합(Mint/Near Mint/Lightly Played/Damaged)\n형식:\n모서리:(관찰)\n흰점:(관찰)\n손상:(관찰)\n등급:(등급)"
        try:
            r = requests.post(f"{self.QURL}/chat/completions", json={
                "model": self.MODEL,
                "messages": [{"role":"user","content":[{"type":"text","text":p},
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],
                "max_tokens": 200, "temperature": 0.1}, timeout=90)
            return r.json().get("choices",[{}])[0].get("message",{}).get("content","분석 실패").strip()
        except Exception as e:
            return f"분석 불가: {e}"

    # ── Gemini API 백엔드 ─────────────────────────

    def _gemini_all(self, crops):
        corners = {}; surface = ""
        with ThreadPoolExecutor(max_workers=5) as pool:
            futs = {pool.submit(self._gemini_one, n, self._b64(img)): n for n, img in crops.items()}
            for f in as_completed(futs):
                n = futs[f]; r = f.result()
                if n == 'surface': surface = r
                else: corners[n] = r
        return {k: corners.get(k, "") for k in ['top_left', 'top_right', 'bottom_left', 'bottom_right']}, surface

    def _gemini_one(self, name, b64):
        if name == 'surface':
            p = ("트레이딩 카드 표면 중앙 확대 사진이다. 객관적으로 관찰하고 답해라.\n"
                 "1.스크래치 2.인쇄결함 3.코팅벗겨짐 4.종합(Mint/Near Mint/Lightly Played/Damaged)\n"
                 "형식:\n스크래치:(관찰)\n인쇄:(관찰)\n코팅:(관찰)\n등급:(등급)")
        else:
            p = ("트레이딩 카드 모서리 확대 사진이다. 객관적으로 관찰하고 답해라.\n"
                 "1.모서리(뾰족/뭉툭) 2.흰점/백화 3.눌림/찌그러짐 4.종합(Mint/Near Mint/Lightly Played/Damaged)\n"
                 "형식:\n모서리:(관찰)\n흰점:(관찰)\n손상:(관찰)\n등급:(등급)")
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
            payload = {
                "contents": [{"parts": [
                    {"text": p},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
                ]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
            }
            r = requests.post(url, json=payload, timeout=90)
            data = r.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "분석 실패")
            return text.strip()
        except Exception as e:
            return f"Gemini 분석 불가: {e}"

    def _combine(self, cen, corners, surface):
        scores = [cen.centering_grade]; notes = []; qc = 0
        if not cen.psa_10_ok:
            notes.append(f"센터링 PSA 10 미달: H {cen.horizontal_worst}% / V {cen.vertical_worst}%")
        for region, text in {**corners, 'surface': surface}.items():
            g = self._parse_grade(text)
            if g is not None:
                scores.append(g); qc += 1
                if g <= 7: notes.append(f"{region} 하락 요소")
        ms = min(scores) if scores else None
        gr = f"PSA {ms}-{min(ms+1,10)}" if ms else "측정 불가"
        conf = "중간" if qc >= 4 else "낮음" if qc >= 1 else "낮음(센터링만)"
        return (gr, ms, conf), (notes if notes else ["감지된 하락 요소 없음"])

    def _parse_grade(self, text):
        tl = text.lower()
        for kw, g in sorted(self.GMAP.items(), key=lambda x: -len(x[0])):
            if kw in tl: return g
        return None

    @staticmethod
    def _b64(img):
        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buf).decode("utf-8")

# ═════════════════════════════════════════════════════════════
# 도감 + 구독
# ═════════════════════════════════════════════════════════════

COLL_DIR = os.path.join(BASE_DIR, "data")
FREE_LIMIT = 50
PREMIUM_PRICE = 4900

def _load_coll():
    p = os.path.join(COLL_DIR, "collection.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    return []

def _save_coll(cards):
    os.makedirs(COLL_DIR, exist_ok=True)
    with open(os.path.join(COLL_DIR, "collection.json"), "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

# ── 사용자/구독 관리 ──────────────────────────────────────────

def _users_path():
    return os.path.join(COLL_DIR, "users.json")

def _load_users():
    p = _users_path()
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def _save_users(users):
    os.makedirs(COLL_DIR, exist_ok=True)
    with open(_users_path(), "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def _get_user(device_id):
    users = _load_users()
    u = users.get(device_id, {"device_id": device_id, "premium": False, "premium_until": None, "joined": datetime.now().isoformat()})
    return u

def _set_user(device_id, user):
    users = _load_users()
    users[device_id] = user
    _save_users(users)

def _is_premium(user):
    if not user.get("premium"): return False
    until = user.get("premium_until")
    if not until: return False
    try:
        return datetime.fromisoformat(until) > datetime.now()
    except: return False

# ═════════════════════════════════════════════════════════════
# Flask
# ═════════════════════════════════════════════════════════════

def create_app():
    from flask import Flask, request, jsonify, send_file
    tdir = os.path.join(os.path.dirname(__file__), "templates")
    sdir = os.path.join(os.path.dirname(__file__), "static")
    app = Flask(__name__, template_folder=tdir, static_folder=sdir)
    grader = CardGrader()
    udir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(udir, exist_ok=True)
    os.makedirs(COLL_DIR, exist_ok=True)

    @app.route("/")
    def index(): return send_file(os.path.join(tdir, "index.html"))

    @app.route("/manifest.json")
    def manifest(): return send_file(os.path.join(sdir, "manifest.json"))

    @app.route("/sw.js")
    def sw(): return send_file(os.path.join(sdir, "sw.js"), mimetype="application/javascript")

    @app.route("/api/box-image/<bid>")
    def box_image(bid):
        from flask import abort
        b = get_box(bid)
        if not b: abort(404)
        img_name = b.get("img","")
        fname = img_name.split("/")[-1] if img_name else f"{bid}.png"
        sdir2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        p = os.path.join(sdir2, "box_images", fname)
        if not os.path.exists(p): abort(404)
        return send_file(p)

    @app.route("/api/boxes")
    def api_boxes(): return jsonify(get_boxes())

    @app.route("/api/boxes/<bid>")
    def api_box(bid):
        b = get_box(bid)
        if not b: return jsonify({"error":"박스 없음"}), 404
        return jsonify({**b, **box_ev(b)})

    @app.route("/api/hit-cards")
    def api_hits(): return jsonify(get_all_hits())

    @app.route("/api/recent-trades")
    def api_trades(): return jsonify(RECENT_TRADES)

    @app.route("/api/analyze", methods=["POST"])
    def api_analyze():
        if "image" not in request.files: return jsonify({"error":"이미지 없음"}), 400
        f = request.files["image"]
        if not f.filename: return jsonify({"error":"파일 미선택"}), 400
        path = os.path.join(udir, "tmp.jpg"); f.save(path)
        try: return jsonify(grader.process(path))
        except Exception as e:
            import traceback; return jsonify({"error":str(e),"trace":traceback.format_exc()}), 500
        finally:
            try: os.remove(path)
            except OSError: pass

    @app.route("/api/collection", methods=["GET"])
    def coll_list():
        device_id = request.args.get("device_id", "anon")
        user = _get_user(device_id)
        all_cards = _load_coll()
        c = [card for card in all_cards if card.get("device_id", "anon") == device_id]
        premium = _is_premium(user)
        return jsonify({"cards": c, "count": len(c), "premium": premium, "limit": None if premium else FREE_LIMIT})

    @app.route("/api/collection", methods=["POST"])
    def coll_add():
        d = request.json or {}
        device_id = d.pop("device_id", "") or "anon"
        user = _get_user(device_id)
        cards = [c for c in _load_coll() if c.get("device_id", "anon") == device_id]
        premium = _is_premium(user)
        if not premium and len(cards) >= FREE_LIMIT:
            return jsonify({"error":"free_limit","limit":FREE_LIMIT,"message":f"무료 도감은 {FREE_LIMIT}장까지 가능합니다. 프리미엄 구독으로 무제한 이용하세요."}), 403
        d["device_id"] = device_id
        d["id"] = (max([c.get("id",0) for c in _load_coll()], default=0)+1) if _load_coll() else 1
        d["added_at"] = datetime.now().isoformat()
        all_cards = _load_coll(); all_cards.append(d); _save_coll(all_cards)
        return jsonify({"status":"ok","id":d["id"],"count":len(cards)+1,"premium":premium,"limit":None if premium else FREE_LIMIT})

    @app.route("/api/collection/<int:cid>", methods=["DELETE"])
    def coll_del(cid):
        cards = _load_coll(); cards = [c for c in cards if c.get("id") != cid]
        _save_coll(cards); return jsonify({"status":"ok","count":len(cards)})

    @app.route("/api/collection/summary")
    def coll_sum():
        device_id = request.args.get("device_id", "anon")
        user = _get_user(device_id)
        cards = [c for c in _load_coll() if c.get("device_id", "anon") == device_id]
        premium = _is_premium(user)
        tc = sum(c.get("cost",0) for c in cards)
        tv = sum(c.get("current_price",0) for c in cards)
        tp = tv - tc
        tr = round(tp/tc*100,1) if tc > 0 else 0
        return jsonify({"count":len(cards),"total_cost":tc,"total_value":tv,"total_profit":tp,"total_roi":tr,"premium":premium,"limit":None if premium else FREE_LIMIT})

    @app.route("/api/collection/refresh", methods=["POST"])
    def coll_refresh():
        data = request.json or {}; updates = data.get("updates",[])
        cards = _load_coll()
        for u in updates:
            for c in cards:
                if c.get("id") == u.get("id"):
                    c["last_price"] = c.get("current_price",0)
                    c["current_price"] = u.get("current_price", c.get("current_price",0))
                    cost = c.get("cost",0)
                    c["profit"] = c["current_price"] - cost if cost > 0 else 0
                    c["roi"] = round(c["profit"]/cost*100,1) if cost > 0 else 0
                    c["price_updated_at"] = datetime.now().isoformat()
                    break
        _save_coll(cards)
        return jsonify({"status":"ok","updated":len(updates),"count":len(cards)})

    @app.route("/api/settle", methods=["POST"])
    def api_settle():
        d = request.json
        return jsonify(calc_settle(int(d.get("sale_price",0)), int(d.get("cost",0))))

    @app.route("/api/subscription", methods=["GET"])
    def sub_status():
        device_id = request.args.get("device_id", "anon")
        user = _get_user(device_id)
        premium = _is_premium(user)
        cards = [c for c in _load_coll() if c.get("device_id", "anon") == device_id]
        return jsonify({
            "device_id": device_id,
            "premium": premium,
            "premium_until": user.get("premium_until"),
            "card_count": len(cards),
            "free_limit": FREE_LIMIT,
            "price": PREMIUM_PRICE,
            "remaining_free": max(0, FREE_LIMIT - len(cards)) if not premium else -1,
        })

    @app.route("/api/subscription/activate", methods=["POST"])
    def sub_activate():
        """Toss Payments 웹훅 또는 수동 활성화."""
        d = request.json or {}
        device_id = d.get("device_id", "")
        if not device_id:
            return jsonify({"error":"device_id 필요"}), 400
        # 실결제 연동 시 여기서 Toss 결제 검증 (orderId, paymentKey, amount)
        # 지금은 웹훅 기반 활성화만 처리
        user = _get_user(device_id)
        user["premium"] = True
        from datetime import timedelta
        user["premium_until"] = (datetime.now() + timedelta(days=30)).isoformat()
        user["activated_at"] = datetime.now().isoformat()
        _set_user(device_id, user)
        return jsonify({"status":"ok","device_id":device_id,"premium":True,"premium_until":user["premium_until"]})

    @app.route("/api/subscription/webhook", methods=["POST"])
    def toss_webhook():
        """Toss Payments 웹훅 수신."""
        d = request.json or {}
        # Toss 결제 완료 콜백: orderId에 device_id 인코딩
        # orderId 형식: "tcg_{device_id}_{timestamp}"
        order_id = d.get("orderId", "")
        status = d.get("status", "")
        if status == "DONE" and order_id.startswith("tcg_"):
            parts = order_id.split("_", 2)
            if len(parts) >= 3:
                device_id = parts[1]
                user = _get_user(device_id)
                user["premium"] = True
                from datetime import timedelta
                user["premium_until"] = (datetime.now() + timedelta(days=30)).isoformat()
                user["payment_key"] = d.get("paymentKey","")
                user["amount"] = d.get("totalAmount", 0)
                _set_user(device_id, user)
                return jsonify({"status":"ok","activated":True,"device_id":device_id})
        return jsonify({"status":"ignored"}), 200

    @app.route("/api/health")
    def health():
        return jsonify({"server":"ok","qwen":grader.qwen,"backend":grader.backend,"model":grader.active_model})

    return app

# Gunicorn이 임포트할 수 있도록 모듈 레벨에서 app 생성
app = create_app()

if __name__ == "__main__":
    gc = CardGrader()
    print(f"Qwen: {'ON' if gc.qwen else 'OFF'}")
    print("Server: http://127.0.0.1:5218")
    app.run(host="127.0.0.1", port=5218, debug=False, threaded=True)
