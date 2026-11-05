"""Draw three generic POS screenshots (no company branding) for scenario tests."""
import sys
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
f = lambda s: ImageFont.truetype(FONT, s)
NAVY, BLUE, BG, CARD, TXT, MUTED, RED, GREEN = "#1F2A44", "#2F6FED", "#F4F6FA", "#FFFFFF", "#1C1C1E", "#6B7280", "#D93F3F", "#1E9E5A"
W, H = 1280, 800

def frame(title):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 64], fill=NAVY)
    d.text((24, 18), "DEMO POS", font=f(24), fill="white")
    d.text((220, 20), title, font=f(22), fill="white")
    d.text((W - 260, 22), "캐셔: 001  |  14:32", font=f(18), fill="#C9D1E3")
    d.rectangle([0, 64, 88, H], fill="#E8ECF4")
    for i, lab in enumerate(["판매", "조회", "환불", "설정"]):
        y = 90 + i * 90
        d.rounded_rectangle([10, y, 78, y + 70], 10, fill=BLUE if i == 0 else CARD)
        d.text((24, y + 24), lab, font=f(18), fill="white" if i == 0 else TXT)
    return im, d

def btn(d, box, text, fill, color="white", size=22):
    d.rounded_rectangle(box, 12, fill=fill)
    x0, y0, x1, y1 = box
    tw = d.textlength(text, font=f(size))
    d.text(((x0 + x1 - tw) / 2, (y0 + y1 - size) / 2 - 2), text, font=f(size), fill=color)

# 1. Sales screen
im, d = frame("판매")
d.rounded_rectangle([108, 84, 760, 780], 12, fill=CARD)
d.text((128, 100), "상품 목록", font=f(20), fill=TXT)
for r, (n, q, p) in enumerate([("아메리카노", 2, "9,000"), ("카페라떼", 1, "5,000"), ("크루아상", 3, "10,500")]):
    y = 150 + r * 64
    d.line([128, y + 56, 740, y + 56], fill="#E5E7EB")
    d.text((128, y + 16), n, font=f(20), fill=TXT); d.text((480, y + 16), f"x{q}", font=f(20), fill=MUTED)
    d.text((620, y + 16), p + "원", font=f(20), fill=TXT)
d.rounded_rectangle([780, 84, 1260, 780], 12, fill=CARD)
for i, (k, v) in enumerate([("소계", "24,500원"), ("할인", "-0원"), ("합계", "24,500원")]):
    d.text((800, 110 + i * 50), k, font=f(22 if i < 2 else 26), fill=MUTED if i < 2 else TXT)
    d.text((1080, 110 + i * 50), v, font=f(22 if i < 2 else 26), fill=TXT)
btn(d, [800, 560, 1020, 640], "쿠폰", CARD, TXT); d.rounded_rectangle([800, 560, 1020, 640], 12, outline="#D1D5DB", width=2)
btn(d, [1030, 560, 1240, 640], "보류", CARD, TXT); d.rounded_rectangle([1030, 560, 1240, 640], 12, outline="#D1D5DB", width=2)
btn(d, [800, 660, 1240, 760], "결제하기", BLUE, size=28)
im.save(f"{OUT}/01-sales.png")

# 2. Transaction lookup
im, d = frame("거래 조회")
d.rounded_rectangle([108, 84, 1260, 160], 12, fill=CARD)
d.rounded_rectangle([128, 100, 700, 144], 8, outline="#D1D5DB", width=2)
d.text((144, 110), "거래번호 또는 날짜로 검색", font=f(18), fill=MUTED)
btn(d, [720, 100, 860, 144], "검색", BLUE, size=20)
d.rounded_rectangle([108, 176, 1260, 780], 12, fill=CARD)
for c, h in zip([128, 400, 640, 880, 1080], ["거래번호", "일시", "금액", "결제수단", "상태"]):
    d.text((c, 196), h, font=f(18), fill=MUTED)
for r, row in enumerate([("T-20261104-0012", "11-04 13:10", "24,500원", "카드", "완료"), ("T-20261104-0011", "11-04 12:55", "8,000원", "현금", "환불")]):
    y = 240 + r * 60
    d.line([128, y + 50, 1240, y + 50], fill="#E5E7EB")
    for c, v in zip([128, 400, 640, 880], row[:4]): d.text((c, y + 14), v, font=f(18), fill=TXT)
    d.rounded_rectangle([1080, y + 8, 1160, y + 40], 14, fill="#E7F6EE" if row[4] == "완료" else "#FDECEC")
    d.text((1098, y + 12), row[4], font=f(16), fill=GREEN if row[4] == "완료" else RED)
im.save(f"{OUT}/02-lookup.png")

# 3. Confirm dialog / error state
im, d = frame("결제")
d.rectangle([88, 64, W, H], fill="#9CA3AF")
d.rounded_rectangle([390, 220, 890, 560], 16, fill=CARD)
d.text((430, 250), "매니저 승인이 필요합니다", font=f(26), fill=TXT)
d.text((430, 300), "할인 금액이 한도를 넘었습니다. 매니저 PIN을 입력해 주세요.", font=f(16), fill=MUTED)
d.rounded_rectangle([430, 350, 850, 400], 8, outline="#D1D5DB", width=2)
d.text((446, 362), "● ● ● ●", font=f(20), fill=TXT)
btn(d, [430, 460, 630, 530], "취소", CARD, TXT); d.rounded_rectangle([430, 460, 630, 530], 12, outline="#D1D5DB", width=2)
btn(d, [650, 460, 850, 530], "승인", BLUE)
d.text((430, 420), "PIN이 올바르지 않습니다.", font=f(16), fill=RED)
im.save(f"{OUT}/03-approval-dialog.png")
print("ok")
