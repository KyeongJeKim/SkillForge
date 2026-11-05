#!/usr/bin/env python3
"""Draw four fictional tablet POS screenshots (1280x800) for SkillForge design tests.

Three screens use the current style (navy header #1F3A5F, teal primary #0F9D8A,
corner radius 12). One screen (03-product-search.png) is an older v1 screen:
gray header, blue #2D6CDF buttons, square corners and a small "v1" label, so a
careful reader can notice the style conflict.

Usage: python3 make_screens.py [out_dir]   (default: this script's folder)
Brand "데모POS" and every product, price and person are fictional.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
W, H = 1280, 800
_fonts = {}


def f(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


# current style
NAVY, TEAL, TEAL_DARK = "#1F3A5F", "#0F9D8A", "#0B7A6B"
BG, CARD, LINE, TXT, MUTED = "#F3F5F8", "#FFFFFF", "#E3E7EE", "#1B2430", "#6B7686"
DISABLED_BG, DISABLED_TX, RED, RED_BG = "#D5DAE1", "#98A1AE", "#D64545", "#FDECEC"
R = 12
# old v1 style
OLD_HEADER, OLD_BLUE, OLD_BG, OLD_LINE = "#8A8F98", "#2D6CDF", "#ECECEC", "#C8C8C8"


def text_c(d, box, s, size, fill):
    x0, y0, x1, y1 = box
    tw = d.textlength(s, font=f(size))
    d.text(((x0 + x1 - tw) / 2, (y0 + y1 - size) / 2 - 1), s, font=f(size), fill=fill)


def text_r(d, x_right, y, s, size, fill):
    d.text((x_right - d.textlength(s, font=f(size)), y), s, font=f(size), fill=fill)


def button(d, box, label, kind="primary", size=22, radius=R):
    colors = {
        "primary": (TEAL, None, "white"),
        "secondary": (CARD, "#C9D0DA", TXT),
        "disabled": (DISABLED_BG, None, DISABLED_TX),
        "danger": (CARD, RED, RED),
        "old": (OLD_BLUE, None, "white"),
        "old2": ("#FFFFFF", "#9A9A9A", "#333333"),
    }
    fill, outline, color = colors[kind]
    if radius:
        d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=2 if outline else 0)
    else:
        d.rectangle(box, fill=fill, outline=outline, width=2 if outline else 0)
    text_c(d, box, label, size, color)


def frame(title, active):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 64], fill=NAVY)
    d.text((24, 17), "데모POS", font=f(26), fill="white")
    d.text((170, 21), "|  " + title, font=f(21), fill="#C8D3E3")
    text_r(d, W - 24, 22, "강남역점  ·  캐셔 김하나(001)  ·  2026-03-12 14:32", 17, "#C8D3E3")
    d.rectangle([0, 64, 92, H], fill="#E7EBF1")
    for i, lab in enumerate(["판매", "결제", "조회", "환불", "설정"]):
        y = 84 + i * 86
        on = lab == active
        d.rounded_rectangle([12, y, 80, y + 70], R, fill=TEAL if on else CARD)
        text_c(d, [12, y, 80, y + 70], lab, 18, "white" if on else TXT)
    return im, d


def card(d, box):
    d.rounded_rectangle(box, R, fill=CARD, outline=LINE, width=1)


def toast(d, msg, y=712, left=112, width=1148):
    w = d.textlength(msg, font=f(19)) + 80
    x0 = left + (width - w) / 2
    d.rounded_rectangle([x0, y, x0 + w, y + 54], R, fill=RED_BG, outline=RED, width=2)
    d.ellipse([x0 + 18, y + 16, x0 + 40, y + 38], fill=RED)
    text_c(d, [x0 + 18, y + 16, x0 + 40, y + 38], "!", 16, "white")
    d.text((x0 + 52, y + 16), msg, font=f(19), fill=RED)


CART = [
    ("아메리카노 (ICE, L)", 2, 4500),
    ("카페라떼 (HOT, R)", 1, 5000),
    ("바닐라 크림 콜드브루", 1, 6300),
    ("버터 크루아상", 3, 3500),
    ("치즈 베이글 + 크림치즈", 1, 4800),
]


def won(n):
    return f"{n:,}원"


# ---------------------------------------------------------------- 01 sale
def sale():
    im, d = frame("판매", "판매")
    # left: category tabs + product grid
    card(d, [112, 84, 760, 780])
    d.rounded_rectangle([132, 100, 560, 144], 10, fill="#F6F7F9", outline="#C9D0DA", width=2)
    d.text((150, 111), "상품명 또는 바코드 검색", font=f(18), fill=MUTED)
    button(d, [572, 100, 740, 144], "카메라 스캔", "secondary", 18)
    tabs = ["전체", "커피", "논커피", "베이커리", "MD상품"]
    x = 132
    for i, t in enumerate(tabs):
        w = d.textlength(t, font=f(18)) + 36
        d.rounded_rectangle([x, 160, x + w, 198], 19, fill=NAVY if i == 1 else "#EEF1F5")
        text_c(d, [x, 160, x + w, 198], t, 18, "white" if i == 1 else TXT)
        x += w + 10
    items = [("아메리카노", 4500), ("카페라떼", 5000), ("바닐라라떼", 5500), ("콜드브루", 5300),
             ("바닐라 크림\n콜드브루", 6300), ("카푸치노", 5000), ("에스프레소", 3800), ("디카페인\n아메리카노", 4800),
             ("헤이즐넛라떼", 5500), ("카라멜\n마키아토", 5900), ("아인슈페너", 6000), ("플랫화이트", 5500)]
    for i, (n, p) in enumerate(items):
        cx, cy = 132 + (i % 4) * 152, 216 + (i // 4) * 150
        sold_out = n == "아인슈페너"
        d.rounded_rectangle([cx, cy, cx + 140, cy + 136], R, fill="#F8FAFB" if not sold_out else "#EEF0F3", outline=LINE)
        d.multiline_text((cx + 14, cy + 16), n, font=f(18), fill=TXT if not sold_out else DISABLED_TX, spacing=4)
        d.text((cx + 14, cy + 100), won(p), font=f(18), fill=TEAL_DARK if not sold_out else DISABLED_TX)
        if sold_out:
            # badge on its own line above the price, so it never touches the price text
            d.rounded_rectangle([cx + 14, cy + 66, cx + 64, cy + 92], 8, fill=DISABLED_BG)
            text_c(d, [cx + 14, cy + 66, cx + 64, cy + 92], "품절", 14, "#5C6573")
    # right: cart
    card(d, [780, 84, 1260, 780])
    d.text((800, 100), "주문 내역", font=f(22), fill=TXT)
    d.rounded_rectangle([1108, 98, 1240, 128], 15, fill="#E6F5F2")
    text_c(d, [1108, 98, 1240, 128], "보류 2건", 15, TEAL_DARK)
    y = 146
    for n, q, p in CART:
        d.text((800, y), n, font=f(18), fill=TXT)
        d.text((800, y + 26), f"{won(p)} x {q}", font=f(15), fill=MUTED)
        text_r(d, 1240, y + 10, won(p * q), 19, TXT)
        d.line([800, y + 54, 1240, y + 54], fill=LINE)
        y += 64
    sub = sum(q * p for _, q, p in CART)
    for i, (k, v) in enumerate([("소계", won(sub)), ("할인", "-0원")]):
        d.text((800, 480 + i * 34), k, font=f(18), fill=MUTED)
        text_r(d, 1240, 480 + i * 34, v, 18, TXT)
    d.line([800, 552, 1240, 552], fill=LINE, width=2)
    d.text((800, 566), "합계", font=f(24), fill=TXT)
    text_r(d, 1240, 562, won(sub), 30, NAVY)
    button(d, [800, 616, 910, 676], "회원", "secondary", 19)
    button(d, [918, 616, 1028, 676], "할인", "disabled", 19)
    button(d, [1036, 616, 1146, 676], "보류", "secondary", 19)
    button(d, [1154, 616, 1240, 676], "삭제", "danger", 19)
    button(d, [800, 690, 1240, 764], f"결제하기  {won(sub)}", "primary", 26)
    toast(d, "등록되지 않은 상품입니다. (바코드: 8800000012345)", y=700, left=112, width=648)
    im.save(OUT / "01-sale.png")


# ---------------------------------------------------------------- 02 payment
def payment():
    im, d = frame("결제", "결제")
    total = sum(q * p for _, q, p in CART)
    card(d, [112, 84, 640, 780])
    d.text((132, 102), "결제 금액", font=f(20), fill=MUTED)
    text_r(d, 620, 96, won(total), 36, NAVY)
    d.line([132, 152, 620, 152], fill=LINE)
    d.text((132, 168), "결제 수단", font=f(20), fill=TXT)
    methods = [("신용/체크카드", False), ("현금", True), ("간편결제", False), ("포인트", False), ("상품권", None), ("분할 결제", False)]
    for i, (m, on) in enumerate(methods):
        bx, by = 132 + (i % 2) * 248, 206 + (i // 2) * 92
        box = [bx, by, bx + 236, by + 80]
        if on is None:
            button(d, box, m, "disabled", 21)
        elif on:
            d.rounded_rectangle(box, R, fill="#E6F5F2", outline=TEAL, width=3)
            text_c(d, box, m, 21, TEAL_DARK)
        else:
            button(d, box, m, "secondary", 21)
    d.text((132, 494), "현금 결제", font=f(20), fill=TXT)
    rows = [("받은 금액", "30,000원", TXT), ("결제 금액", won(total), TXT), ("부족 금액", won(total - 30000), RED)]
    for i, (k, v, c) in enumerate(rows):
        d.text((132, 536 + i * 44), k, font=f(19), fill=MUTED)
        text_r(d, 620, 534 + i * 44, v, 22, c)
    d.rounded_rectangle([132, 680, 620, 760], R, fill="#F6F7F9")
    d.text((152, 694), "받은 금액이 결제 금액보다 적습니다.", font=f(17), fill=RED)
    d.text((152, 722), "금액을 다시 입력하거나 분할 결제를 선택하세요.", font=f(16), fill=MUTED)
    # keypad
    card(d, [660, 84, 1260, 780])
    d.rounded_rectangle([680, 102, 1240, 172], R, fill="#F6F7F9", outline=TEAL, width=2)
    d.text((700, 118), "받은 금액", font=f(18), fill=MUTED)
    text_r(d, 1220, 112, "30,000", 34, TXT)
    quick = ["+1만", "+3만", "+5만", "딱 맞게"]
    for i, q in enumerate(quick):
        button(d, [680 + i * 142, 186, 680 + i * 142 + 130, 236], q, "secondary", 18)
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "00", "0", "←"]
    for i, k in enumerate(keys):
        kx, ky = 680 + (i % 3) * 191, 252 + (i // 3) * 92
        button(d, [kx, ky, kx + 178, ky + 80], k, "secondary", 28)
    button(d, [680, 628, 900, 760], "취소", "secondary", 24)
    button(d, [916, 628, 1240, 760], "결제 완료", "disabled", 26)
    im.save(OUT / "02-payment.png")


# ---------------------------------------------------------------- 03 product search (OLD v1)
def product_search_v1():
    im = Image.new("RGB", (W, H), OLD_BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 56], fill=OLD_HEADER)
    d.text((20, 14), "데모POS", font=f(24), fill="white")
    d.text((150, 18), "상품 조회", font=f(20), fill="white")
    d.rectangle([250, 18, 282, 40], fill="#6E737B")
    text_c(d, [250, 18, 282, 40], "v1", 14, "white")
    text_r(d, W - 20, 18, "캐셔 001  14:35", 17, "white")
    d.rectangle([0, 56, 92, H], fill="#D9D9D9")
    for i, lab in enumerate(["판매", "결제", "조회", "환불", "설정"]):
        y = 70 + i * 80
        on = lab == "조회"
        d.rectangle([8, y, 84, y + 66], fill=OLD_BLUE if on else "#FFFFFF", outline=OLD_LINE)
        text_c(d, [8, y, 84, y + 66], lab, 18, "white" if on else "#333333")
    # search bar
    d.rectangle([108, 72, 1264, 140], fill="#FFFFFF", outline=OLD_LINE)
    d.rectangle([124, 86, 700, 126], fill="#FFFFFF", outline="#9A9A9A", width=1)
    d.text((136, 95), "크루아상", font=f(19), fill="#222222")
    for i, opt in enumerate(["상품명", "바코드", "상품코드"]):
        bx = 716 + i * 110
        d.rectangle([bx, 86, bx + 100, 126], fill="#DDE6F7" if i == 0 else "#FFFFFF", outline="#9A9A9A")
        text_c(d, [bx, 86, bx + 100, 126], opt, 17, "#333333")
    button(d, [1060, 86, 1248, 126], "검색", "old", 19, radius=0)
    # results table
    d.rectangle([108, 152, 1264, 700], fill="#FFFFFF", outline=OLD_LINE)
    cols = [(124, "상품코드"), (284, "상품명"), (604, "분류"), (744, "판매가"), (894, "재고"), (994, "상태"), (1104, "")]
    d.rectangle([109, 153, 1263, 193], fill="#F0F0F0")
    for x, h in cols:
        d.text((x, 163), h, font=f(17), fill="#555555")
    rows = [("BK-0101", "버터 크루아상", "베이커리", "3,500원", "18", "판매중"),
            ("BK-0102", "아몬드 크루아상", "베이커리", "4,200원", "6", "판매중"),
            ("BK-0103", "초코 크루아상", "베이커리", "4,000원", "0", "품절"),
            ("BK-0110", "크루아상 샌드위치 (햄치즈)", "베이커리", "6,800원", "4", "판매중"),
            ("BK-0111", "미니 크루아상 5입", "베이커리", "7,500원", "2", "판매중"),
            ("MD-0405", "크루아상 쿠션 키링", "MD상품", "12,000원", "-", "판매중지")]
    for r, row in enumerate(rows):
        y = 200 + r * 72
        d.line([110, y + 64, 1262, y + 64], fill="#E0E0E0")
        for (x, _), v in zip(cols, row):
            color = "#C62828" if v in ("품절", "판매중지") else "#222222"
            d.text((x, y + 22), v, font=f(18), fill=color)
        ok = row[5] == "판매중"
        if ok:
            button(d, [1104, y + 12, 1248, y + 54], "담기", "old", 18, radius=0)
        else:
            d.rectangle([1104, y + 12, 1248, y + 54], fill="#E4E4E4", outline="#C8C8C8")
            text_c(d, [1104, y + 12, 1248, y + 54], "담기", 18, "#A0A0A0")
    d.text((124, 660), "검색 결과 6건", font=f(16), fill="#666666")
    button(d, [108, 716, 400, 784], "닫기", "old2", 22, radius=0)
    button(d, [972, 716, 1264, 784], "선택 상품 담기", "old", 22, radius=0)
    im.save(OUT / "03-product-search.png")


# ---------------------------------------------------------------- 04 refund dialog
def refund_dialog():
    im, d = frame("환불", "환불")
    card(d, [112, 84, 1260, 780])
    d.text((132, 102), "거래 상세  T-20260312-0087", font=f(22), fill=TXT)
    for i, (k, v) in enumerate([("거래 일시", "2026-03-12 11:08"), ("결제 수단", "신용카드 (승인 30418822)"), ("결제 금액", "30,800원")]):
        d.text((132, 150 + i * 36), k, font=f(18), fill=MUTED)
        d.text((300, 150 + i * 36), v, font=f(18), fill=TXT)
    for i, (n, q, p) in enumerate(CART[:4]):
        y = 280 + i * 54
        d.text((132, y), n, font=f(18), fill=TXT)
        text_r(d, 1240, y, f"x{q}  {won(p * q)}", 18, TXT)
        d.line([132, y + 40, 1240, y + 40], fill=LINE)
    # dim overlay
    overlay = Image.new("RGBA", (W, H), (15, 25, 40, 150))
    im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(im)
    box = [340, 130, 940, 690]
    d.rounded_rectangle(box, R, fill=CARD)
    d.text((372, 158), "환불하시겠습니까?", font=f(26), fill=TXT)
    d.text((372, 200), "카드 승인이 취소되며 되돌릴 수 없습니다.", font=f(17), fill=MUTED)
    d.line([372, 236, 908, 236], fill=LINE)
    info = [("거래번호", "T-20260312-0087"), ("환불 대상", "전체 (4개 품목)"), ("환불 금액", "30,800원")]
    for i, (k, v) in enumerate(info):
        d.text((372, 254 + i * 40), k, font=f(18), fill=MUTED)
        text_r(d, 908, 252 + i * 40, v, 22 if k == "환불 금액" else 18, RED if k == "환불 금액" else TXT)
    d.text((372, 384), "환불 사유", font=f(18), fill=TXT)
    d.rounded_rectangle([372, 412, 908, 456], 10, outline="#C9D0DA", width=2, fill=CARD)
    d.text((388, 422), "고객 단순 변심", font=f(18), fill=TXT)
    d.polygon([(880, 428), (896, 428), (888, 440)], fill=MUTED)
    d.text((372, 474), "매니저 승인 PIN", font=f(18), fill=TXT)
    for i in range(4):
        bx = 372 + i * 70
        d.rounded_rectangle([bx, 502, bx + 58, 556], 10, outline=RED if i < 4 else "#C9D0DA", width=2, fill=CARD)
        text_c(d, [bx, 502, bx + 58, 556], "●", 20, TXT)
    d.text((372, 566), "PIN이 일치하지 않습니다. (2/5회)", font=f(16), fill=RED)
    button(d, [372, 610, 630, 670], "취소", "secondary", 22)
    button(d, [650, 610, 908, 670], "환불 진행", "primary", 22)
    im.save(OUT / "04-refund-confirm.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    sale()
    payment()
    product_search_v1()
    refund_dialog()
    print("wrote 4 POS screens to", OUT)
