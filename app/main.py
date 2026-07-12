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
    {"id":"blackbolt","name":"블랙볼트","code":"SV11B","lang":"kr","release":"2026-04","packs":30,"cpp":5,"price_kr":135000,"price_jp":235000,"desc":"티탱크 ex, 두빅굴, 무쿠무쿠",
     "hits":[{"n":"티탱크 ex SR","r":"SR","p":45000,"rate":"1/30"},{"n":"두빅굴 SAR","r":"SAR","p":80000,"rate":"1/60"},{"n":"무쿠무쿠 SAR","r":"SAR","p":60000,"rate":"1/60"},{"n":"티탱크 ex AR","r":"AR","p":12000,"rate":"1/10"}]},
    {"id":"whiteflare","name":"화이트플레어","code":"SV11A","lang":"kr","release":"2026-04","packs":30,"cpp":5,"price_kr":110000,"price_jp":200000,"desc":"레시라무 ex, 가디안, 수댕이",
     "hits":[{"n":"레시라무 ex SR","r":"SR","p":120000,"rate":"1/30"},{"n":"가디안 SAR","r":"SAR","p":90000,"rate":"1/60"},{"n":"수댕이 SAR","r":"SAR","p":25000,"rate":"1/60"},{"n":"레시라무 ex AR","r":"AR","p":15000,"rate":"1/10"}]},
    {"id":"infernox","name":"인페르노X","code":"SV10a","lang":"kr","release":"2026-03","packs":30,"cpp":5,"price_kr":63000,"price_jp":120000,"desc":"리자몽 ex, 빛나, 푸크린",
     "hits":[{"n":"리자몽 ex SR","r":"SR","p":35000,"rate":"1/30"},{"n":"리자몽 ex SAR","r":"SAR","p":120000,"rate":"1/90"},{"n":"빛나 SAR","r":"SAR","p":18000,"rate":"1/60"},{"n":"푸크린 AR","r":"AR","p":3000,"rate":"1/10"}]},
    {"id":"nihilzero","name":"니힐제로","code":"SV12","lang":"kr","release":"2026-06","packs":30,"cpp":5,"price_kr":35000,"price_jp":80000,"desc":"니힐제로, 신규 메카닉",
     "hits":[{"n":"니힐제로 SR","r":"SR","p":15000,"rate":"1/30"},{"n":"니힐제로 SAR","r":"SAR","p":40000,"rate":"1/60"}]},
    {"id":"abyss","name":"어비스아이","code":"SV10b","lang":"kr","release":"2026-03","packs":30,"cpp":5,"price_kr":48000,"price_jp":95000,"desc":"메가다크라이 ex, 메가제라오라 ex",
     "hits":[{"n":"메가다크라이 ex SR","r":"SR","p":50000,"rate":"1/30"},{"n":"메가제라오라 ex SAR","r":"SAR","p":35000,"rate":"1/60"},{"n":"이슬의 기력 SAR","r":"SAR","p":12000,"rate":"1/60"},{"n":"무쿠무쿠 SAR","r":"SAR","p":40000,"rate":"1/60"}]},
    {"id":"ninjaspinner","name":"닌자스피너","code":"SV9a","lang":"kr","release":"2026-02","packs":30,"cpp":5,"price_kr":40000,"price_jp":75000,"desc":"한카리아스 ex, 루카리오",
     "hits":[{"n":"한카리아스 ex SR","r":"SR","p":25000,"rate":"1/30"},{"n":"루카리오 SAR","r":"SAR","p":18000,"rate":"1/60"}]},
    {"id":"151","name":"151","code":"SV3a","lang":"kr","release":"2025-09","packs":30,"cpp":5,"price_kr":50000,"price_jp":90000,"desc":"관동 151종, 뮤츠 ex, 나옹",
     "hits":[{"n":"뮤츠 ex SR","r":"SR","p":35000,"rate":"1/30"},{"n":"뮤츠 ex SAR","r":"SAR","p":80000,"rate":"1/90"},{"n":"나옹 SAR","r":"SAR","p":50000,"rate":"1/90"},{"n":"이브이 master","r":"master","p":200000,"rate":"1/300"}]},
    {"id":"vstar","name":"VSTAR 유니버스","code":"S12a","lang":"kr","release":"2025-01","packs":30,"cpp":5,"price_kr":35000,"price_jp":70000,"desc":"아르세우스 VSTAR, 리피아 VSTAR",
     "hits":[{"n":"아르세우스 VSTAR SR","r":"SR","p":18000,"rate":"1/30"},{"n":"리피아 VSTAR SR","r":"SR","p":12000,"rate":"1/30"},{"n":"디안시 SR","r":"SR","p":2500,"rate":"1/30"}]},
    {"id":"megadream","name":"MEGA 드림 ex","code":"SV9b","lang":"kr","release":"2026-02","packs":30,"cpp":5,"price_kr":15000,"price_jp":35000,"desc":"메가리자몽X ex, 피카츄 ex",
     "hits":[{"n":"메가리자몽X ex SR","r":"SR","p":30000,"rate":"1/30"},{"n":"피카츄 ex SR","r":"SR","p":95000,"rate":"1/30"},{"n":"피카츄 ex SAR","r":"SAR","p":145000,"rate":"1/90"}]},
    {"id":"rocket","name":"로켓단의 영광","code":"SV8a","lang":"kr","release":"2026-01","packs":30,"cpp":5,"price_kr":46000,"price_jp":85000,"desc":"악비라르 ex, 블래키 VMAX",
     "hits":[{"n":"악비라르 ex SR","r":"SR","p":22000,"rate":"1/30"},{"n":"블래키 VMAX R","r":"R","p":730000,"rate":"1/200"}]},
    {"id":"terastal","name":"테라스탈 페스타 ex","code":"SV8","lang":"kr","release":"2025-12","packs":30,"cpp":5,"price_kr":30000,"price_jp":60000,"desc":"님피아 ex, 테라스탈",
     "hits":[{"n":"님피아 ex SR","r":"SR","p":75000,"rate":"1/30"}]},
    {"id":"ebreaker","name":"초전브레이커","code":"SV10","lang":"kr","release":"2026-03","packs":30,"cpp":5,"price_kr":44000,"price_jp":85000,"desc":"피카츄 ex, 티탱크 ex",
     "hits":[{"n":"피카츄 ex SR","r":"SR","p":145000,"rate":"1/30"},{"n":"피카츄 ex SAR","r":"SAR","p":200000,"rate":"1/90"}]},
]

def get_boxes(): return BOXES
def get_box(bid): return next((b for b in BOXES if b["id"] == bid), None)

def get_all_hits():
    out = []
    for b in BOXES:
        for h in b.get("hits", []):
            out.append({"name": h["n"], "rarity": h["r"], "est_price": h["p"], "pull_rate": h["rate"],
                        "box_id": b["id"], "box_name": b["name"], "code": b["code"]})
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
        self.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")
        self.backend = "none"
        try:
            if requests.get(f"{self.QURL}/models", timeout=3).status_code == 200:
                self.qwen = True
                self.backend = "qwen"
        except:
            pass
        if not self.qwen and self.gemini_key:
            self.backend = "gemini"

    def process(self, path):
        img = cv2.imread(path)
        if img is None: raise ValueError("이미지 불가")
        h, w = img.shape[:2]
        if max(h, w) > 1200:
            s = 1200 / max(h, w); img = cv2.resize(img, (int(w * s), int(h * s)))
        pts = self._detect(img)
        card = self._correct(img, pts) if pts is not None else cv2.resize(img, (self.CW, self.CH))
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
        return {"centering": asdict(cen), "qwen_corners": corners, "qwen_surface": surface,
                "overall_grade_range": ov[0], "overall_min_score": ov[1], "overall_confidence": ov[2],
                "notes": notes, "annotated_b64": self._b64(ann), "corrected_b64": self._b64(card),
                "backend": self.backend,
                "disclaimer": "참고용이며 실제 PSA/BGS/CGC 결과와 다를 수 있습니다."}

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
# 도감
# ═════════════════════════════════════════════════════════════

COLL_DIR = os.path.join(BASE_DIR, "data")

def _load_coll():
    p = os.path.join(COLL_DIR, "collection.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    return []

def _save_coll(cards):
    os.makedirs(COLL_DIR, exist_ok=True)
    with open(os.path.join(COLL_DIR, "collection.json"), "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

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

    @app.route("/api/boxes")
    def api_boxes(): return jsonify(get_boxes())

    @app.route("/api/boxes/<bid>")
    def api_box(bid):
        b = get_box(bid)
        if not b: return jsonify({"error":"박스 없음"}), 404
        return jsonify({**b, **box_ev(b)})

    @app.route("/api/hit-cards")
    def api_hits(): return jsonify(get_all_hits())

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
        c = _load_coll(); return jsonify({"cards": c, "count": len(c)})

    @app.route("/api/collection", methods=["POST"])
    def coll_add():
        d = request.json; cards = _load_coll()
        d["id"] = (max([c.get("id",0) for c in cards], default=0)+1) if cards else 1
        d["added_at"] = datetime.now().isoformat()
        cards.append(d); _save_coll(cards)
        return jsonify({"status":"ok","id":d["id"],"count":len(cards)})

    @app.route("/api/collection/<int:cid>", methods=["DELETE"])
    def coll_del(cid):
        cards = _load_coll(); cards = [c for c in cards if c.get("id") != cid]
        _save_coll(cards); return jsonify({"status":"ok","count":len(cards)})

    @app.route("/api/collection/summary")
    def coll_sum():
        cards = _load_coll()
        tc = sum(c.get("cost",0) for c in cards)
        tv = sum(c.get("current_price",0) for c in cards)
        tp = tv - tc
        tr = round(tp/tc*100,1) if tc > 0 else 0
        return jsonify({"count":len(cards),"total_cost":tc,"total_value":tv,"total_profit":tp,"total_roi":tr})

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

    @app.route("/api/health")
    def health():
        return jsonify({"server":"ok","qwen":grader.qwen,"backend":grader.backend,"model":grader.MODEL})

    return app

if __name__ == "__main__":
    app = create_app()
    gc = CardGrader()
    print(f"Qwen: {'ON' if gc.qwen else 'OFF'}")
    print("Server: http://127.0.0.1:5218")
    app.run(host="127.0.0.1", port=5218, debug=False, threaded=True)
