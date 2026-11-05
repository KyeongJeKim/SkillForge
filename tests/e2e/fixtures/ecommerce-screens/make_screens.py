#!/usr/bin/env python3
"""Draw three fictional shopping-mall admin screenshots (1440x900) for SkillForge design tests.

01-product-list.png    상품 목록: filter panel, bulk actions, data table, pagination
02-product-register.png 상품 등록: sectioned form, option table, validation error
03-promotion-list.png  프로모션 목록: status tabs, status badges, table

All three share one admin style (dark sidebar, indigo primary #3B5BDB, radius 8).
Usage: python3 make_screens.py [out_dir]   (default: this script's folder)
"한빛몰" and every product, number and person are fictional.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
W, H = 1440, 900
_fonts = {}


def f(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


SIDE, SIDE_TX, SIDE_ON = "#1E2430", "#AEB6C4", "#2C3446"
PRIMARY, PRIMARY_LIGHT = "#3B5BDB", "#E8EDFD"
BG, CARD, LINE, TXT, MUTED = "#F5F6F8", "#FFFFFF", "#E4E7EC", "#1D2433", "#6A7385"
RED, RED_BG = "#D92D20", "#FEF3F2"
BADGE = {
    "진행중": ("#E7F6EC", "#167A3E"),
    "예정": ("#E8EDFD", "#3B5BDB"),
    "종료": ("#EEF0F3", "#5F6878"),
    "임시저장": ("#FFF4E5", "#B54708"),
    "판매중": ("#E7F6EC", "#167A3E"),
    "품절": ("#FEF3F2", "#D92D20"),
    "판매중지": ("#EEF0F3", "#5F6878"),
    "승인대기": ("#FFF4E5", "#B54708"),
}
R = 8


def text_c(d, box, s, size, fill):
    x0, y0, x1, y1 = box
    tw = d.textlength(s, font=f(size))
    d.text(((x0 + x1 - tw) / 2, (y0 + y1 - size) / 2 - 1), s, font=f(size), fill=fill)


def text_r(d, xr, y, s, size, fill):
    d.text((xr - d.textlength(s, font=f(size)), y), s, font=f(size), fill=fill)


def button(d, box, label, kind="primary", size=15):
    fill, outline, color = {
        "primary": (PRIMARY, None, "white"),
        "secondary": (CARD, "#CDD2DA", TXT),
        "danger": (CARD, "#F3B4AE", RED),
        "disabled": ("#E9ECF0", None, "#A3AAB6"),
    }[kind]
    d.rounded_rectangle(box, R, fill=fill, outline=outline, width=1 if outline else 0)
    text_c(d, box, label, size, color)


def badge(d, x, y, label):
    bg, fg = BADGE[label]
    w = d.textlength(label, font=f(13)) + 20
    d.rounded_rectangle([x, y, x + w, y + 24], 12, fill=bg)
    text_c(d, [x, y, x + w, y + 24], label, 13, fg)


def field(d, box, value="", placeholder="", error=False, select=False):
    d.rounded_rectangle(box, R, fill=CARD, outline=RED if error else "#CDD2DA", width=2 if error else 1)
    s, c = (value, TXT) if value else (placeholder, "#A3AAB6")
    d.text((box[0] + 12, (box[1] + box[3]) / 2 - 9), s, font=f(15), fill=c)
    if select:
        x, y = box[2] - 22, (box[1] + box[3]) / 2 - 3
        d.polygon([(x, y), (x + 10, y), (x + 5, y + 7)], fill=MUTED)


def checkbox(d, x, y, on=False):
    d.rounded_rectangle([x, y, x + 18, y + 18], 4, fill=PRIMARY if on else CARD, outline=PRIMARY if on else "#B8BFCA")
    if on:
        d.line([(x + 4, y + 9), (x + 8, y + 13), (x + 14, y + 5)], fill="white", width=2)


def frame(active, crumbs, title):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 220, H], fill=SIDE)
    d.text((24, 22), "한빛몰", font=f(22), fill="white")
    d.text((100, 27), "파트너 어드민", font=f(14), fill=SIDE_TX)
    menu = [("대시보드", []), ("상품 관리", ["상품 목록", "상품 등록", "카테고리"]), ("주문/배송", []),
            ("프로모션", ["프로모션 목록", "쿠폰"]), ("고객 문의", []), ("정산", []), ("설정", [])]
    y = 80
    for group, subs in menu:
        d.text((24, y), group, font=f(15), fill="white" if any(s == active for s in subs) else SIDE_TX)
        y += 36
        for s in subs:
            if s == active:
                d.rounded_rectangle([12, y - 6, 208, y + 26], R, fill=SIDE_ON)
                d.rectangle([12, y - 6, 15, y + 26], fill=PRIMARY)
            d.text((40, y), s, font=f(14), fill="white" if s == active else "#8A93A3")
            y += 34
    # top bar
    d.rectangle([220, 0, W, 60], fill=CARD)
    d.line([220, 60, W, 60], fill=LINE)
    d.text((244, 20), " > ".join(crumbs), font=f(14), fill=MUTED)
    text_r(d, W - 24, 20, "김민지 (패션MD팀)  |  로그아웃", 14, MUTED)
    d.text((244, 80), title, font=f(24), fill=TXT)
    return im, d


# ---------------------------------------------------------------- 01 product list
def product_list():
    im, d = frame("상품 목록", ["상품 관리", "상품 목록"], "상품 목록")
    button(d, [1300, 78, 1416, 114], "+ 상품 등록", "primary")
    button(d, [1180, 78, 1290, 114], "엑셀 다운로드", "secondary", 14)
    # filters
    d.rounded_rectangle([244, 130, 1416, 262], R, fill=CARD, outline=LINE)
    labels = [("검색어", 264, 150), ("카테고리", 744, 150), ("판매 상태", 264, 206), ("등록일", 744, 206)]
    for lab, x, y in labels:
        d.text((x, y + 8), lab, font=f(14), fill=MUTED)
    field(d, [344, 148, 724, 184], "린넨")
    field(d, [824, 148, 1060, 184], "여성 > 상의", select=True)
    for i, (s, on) in enumerate([("전체", False), ("판매중", True), ("품절", True), ("판매중지", False)]):
        x = 344 + i * 92
        checkbox(d, x, 213, on)
        d.text((x + 26, 212), s, font=f(14), fill=TXT)
    field(d, [824, 204, 960, 240], "2026-02-01")
    d.text((968, 212), "~", font=f(15), fill=MUTED)
    field(d, [988, 204, 1124, 240], "2026-03-31")
    button(d, [1240, 204, 1320, 240], "초기화", "secondary", 14)
    button(d, [1328, 204, 1400, 240], "검색", "primary", 14)
    # table
    d.rounded_rectangle([244, 278, 1416, 880], R, fill=CARD, outline=LINE)
    d.text((264, 296), "검색 결과 128건", font=f(15), fill=TXT)
    d.text((394, 297), "· 2건 선택됨", font=f(14), fill=PRIMARY)
    button(d, [1088, 290, 1176, 320], "판매중지", "secondary", 13)
    button(d, [1184, 290, 1272, 320], "가격 일괄변경", "secondary", 13)
    button(d, [1280, 290, 1396, 320], "선택 삭제", "danger", 13)
    cols = [(264, ""), (300, "상품코드"), (450, "이미지"), (520, "상품명"), (860, "판매가"), (960, "할인가"),
            (1060, "재고"), (1130, "상태"), (1230, "등록일"), (1340, "관리")]
    d.rectangle([245, 334, 1415, 372], fill="#F8F9FB")
    d.line([245, 372, 1415, 372], fill=LINE)
    checkbox(d, 264, 344)
    for x, h in cols[1:]:
        d.text((x, 344), h, font=f(14), fill=MUTED)
    rows = [
        ("HB-TOP-26S-0412", "[데일리핏] 프렌치 린넨 오버핏 셔츠", "49,000", "39,200", "312", "판매중", "03-04", True),
        ("HB-TOP-26S-0415", "[데일리핏] 린넨 반팔 셔츠 (3color)", "39,000", "35,100", "0", "품절", "03-05", True),
        ("HB-TOP-26S-0420", "린넨 블렌드 스트라이프 블라우스", "45,000", "-", "88", "판매중", "03-06", False),
        ("HB-TOP-26S-0426", "[데일리핏] 린넨 크롭 셔츠자켓", "69,000", "55,200", "41", "판매중", "03-09", False),
        ("HB-TOP-26S-0433", "워싱 린넨 헨리넥 티셔츠", "29,000", "-", "7", "승인대기", "03-11", False),
        ("HB-TOP-26S-0438", "린넨 셔링 퍼프 블라우스", "42,000", "33,600", "156", "판매중", "03-12", False),
        ("HB-TOP-26S-0441", "[데일리핏] 린넨 베스트 (아이보리)", "35,000", "-", "0", "판매중지", "03-13", False),
        ("HB-TOP-26S-0447", "오버핏 린넨 롱셔츠 원피스", "59,000", "47,200", "64", "판매중", "03-16", False),
    ]
    for r, (code, name, price, sale, stock, st, dt, sel) in enumerate(rows):
        y = 372 + r * 56
        if sel:
            d.rectangle([245, y + 1, 1415, y + 56], fill="#F4F6FE")
        d.line([245, y + 56, 1415, y + 56], fill=LINE)
        checkbox(d, 264, y + 19, sel)
        d.text((300, y + 19), code, font=f(13), fill=MUTED)
        d.rounded_rectangle([450, y + 8, 490, y + 48], 6, fill="#E9ECF0")
        d.text((520, y + 18), name, font=f(15), fill=TXT)
        text_r(d, 920, y + 18, price, 15, TXT)
        text_r(d, 1020, y + 18, sale, 15, RED if sale != "-" else MUTED)
        d.text((1060, y + 18), stock, font=f(15), fill=RED if stock == "0" else TXT)
        badge(d, 1130, y + 16, st)
        d.text((1230, y + 18), "2026-" + dt, font=f(14), fill=MUTED)
        button(d, [1340, y + 13, 1396, y + 43], "수정", "secondary", 13)
    # pagination
    py = 836
    for i, p in enumerate(["<", "1", "2", "3", "4", "5", "...", "16", ">"]):
        x = 640 + i * 40
        on = p == "1"
        d.rounded_rectangle([x, py, x + 32, py + 32], 6, fill=PRIMARY if on else CARD, outline=None if on else LINE)
        text_c(d, [x, py, x + 32, py + 32], p, 14, "white" if on else TXT)
    d.text((1240, py + 7), "20개씩 보기", font=f(14), fill=MUTED)
    im.save(OUT / "01-product-list.png")


# ---------------------------------------------------------------- 02 product register
def product_register():
    im, d = frame("상품 등록", ["상품 관리", "상품 등록"], "상품 등록")
    d.text((372, 88), "* 표시는 필수 입력 항목입니다.", font=f(13), fill=MUTED)
    # left form card
    d.rounded_rectangle([244, 130, 1060, 880], R, fill=CARD, outline=LINE)
    d.text((268, 148), "1. 기본 정보", font=f(18), fill=TXT)
    rows = [("카테고리 *", "여성 > 하의 > 데님", None, True), ("상품명 *", "[데일리핏] 원턱 와이드 데님팬츠", None, False),
            ("판매가 *", "45,000", None, False), ("할인가", "", "할인가는 판매가보다 낮아야 합니다.", False)]
    y = 188
    for lab, val, err, sel in rows:
        d.text((268, y + 9), lab, font=f(14), fill=TXT)
        if lab == "할인가":
            field(d, [400, y, 640, y + 38], "52,000", error=True)
            d.text((652, y + 9), "원", font=f(14), fill=MUTED)
            d.text((400, y + 44), err, font=f(13), fill=RED)
            y += 70
        else:
            field(d, [400, y, 1036 if lab != "판매가 *" else 640, y + 38], val, select=sel)
            if lab == "판매가 *":
                d.text((652, y + 9), "원", font=f(14), fill=MUTED)
            y += 52
    d.line([268, y + 4, 1036, y + 4], fill=LINE)
    y += 22
    d.text((268, y), "2. 옵션", font=f(18), fill=TXT)
    button(d, [944, y - 4, 1036, y + 26], "+ 옵션 추가", "secondary", 13)
    y += 40
    d.rectangle([268, y, 1036, y + 34], fill="#F8F9FB")
    for x, h in [(284, "색상"), (424, "사이즈"), (564, "추가금"), (704, "재고"), (844, "판매")]:
        d.text((x, y + 9), h, font=f(14), fill=MUTED)
    opts = [("연청", "S", "0", "40", True), ("연청", "M", "0", "55", True), ("중청", "M", "0", "38", True),
            ("흑청", "L", "0", "20", True), ("흑청", "XL", "0", "0", False)]
    for i, (c, s, add, st, on) in enumerate(opts):
        oy = y + 34 + i * 44
        d.line([268, oy + 44, 1036, oy + 44], fill=LINE)
        for x, v in [(284, c), (424, s), (564, add + "원"), (704, st)]:
            d.text((x, oy + 13), v, font=f(15), fill=TXT if not (v == "0" and x == 704) else RED)
        tx = 844
        d.rounded_rectangle([tx, oy + 12, tx + 40, oy + 32], 10, fill=PRIMARY if on else "#C9CFD8")
        cx = tx + 30 if on else tx + 10
        d.ellipse([cx - 8, oy + 14, cx + 8, oy + 30], fill="white")
    y = y + 34 + len(opts) * 44 + 24
    d.text((268, y), "3. 상세 설명", font=f(18), fill=TXT)
    y += 36
    d.rounded_rectangle([268, y, 1036, 862], R, fill="#FAFBFC", outline="#CDD2DA")
    d.rectangle([269, y + 1, 1035, y + 36], fill="#F1F3F6")
    for i, t in enumerate(["B", "I", "U", "H2", "이미지", "표", "링크"]):
        d.text((284 + i * 56, y + 9), t, font=f(14), fill=MUTED)
    d.text((284, y + 52), "원턱 디테일로 허리 핏을 잡아주는 와이드 데님팬츠입니다.", font=f(15), fill=TXT)
    # right side card
    d.rounded_rectangle([1080, 130, 1416, 520], R, fill=CARD, outline=LINE)
    d.text((1100, 148), "대표 이미지 *", font=f(16), fill=TXT)
    d.rounded_rectangle([1100, 184, 1396, 400], R, fill="#F8F9FB", outline="#B8BFCA")
    text_c(d, [1100, 250, 1396, 280], "이미지를 끌어다 놓거나 클릭", 14, MUTED)
    text_c(d, [1100, 282, 1396, 310], "1000x1000 이상, JPG/PNG, 10MB 이하", 12, "#A3AAB6")
    d.text((1100, 418), "판매 상태", font=f(15), fill=TXT)
    for i, (s, on) in enumerate([("판매중", False), ("판매대기", True)]):
        x = 1100 + i * 110
        d.ellipse([x, 452, x + 18, 470], outline=PRIMARY if on else "#B8BFCA", width=2, fill=CARD)
        if on:
            d.ellipse([x + 5, 457, x + 13, 465], fill=PRIMARY)
        d.text((x + 26, 451), s, font=f(14), fill=TXT)
    d.rounded_rectangle([1080, 536, 1416, 700], R, fill=RED_BG, outline="#F3B4AE")
    d.text((1100, 554), "저장 전 확인해 주세요 (2)", font=f(15), fill=RED)
    d.text((1100, 590), "· 할인가가 판매가보다 높습니다.", font=f(14), fill=RED)
    d.text((1100, 620), "· 상품정보제공고시가 비어 있습니다.", font=f(14), fill=RED)
    button(d, [1080, 776, 1240, 820], "임시저장", "secondary", 15)
    button(d, [1256, 776, 1416, 820], "등록 요청", "disabled", 15)
    button(d, [1080, 832, 1416, 872], "미리보기", "secondary", 14)
    im.save(OUT / "02-product-register.png")


# ---------------------------------------------------------------- 03 promotion list
def promotion_list():
    im, d = frame("프로모션 목록", ["프로모션", "프로모션 목록"], "프로모션 목록")
    button(d, [1280, 78, 1416, 114], "+ 프로모션 만들기", "primary", 14)
    tabs = [("전체", 24), ("진행중", 3), ("예정", 4), ("종료", 15), ("임시저장", 2)]
    x = 244
    for i, (t, n) in enumerate(tabs):
        label = f"{t} {n}"
        w = d.textlength(label, font=f(15)) + 28
        on = i == 0
        d.text((x + 14, 140), label, font=f(15), fill=PRIMARY if on else MUTED)
        if on:
            d.rectangle([x, 168, x + w, 171], fill=PRIMARY)
        x += w + 8
    d.line([244, 171, 1416, 171], fill=LINE)
    field(d, [1116, 130, 1340, 162], "", "프로모션명 검색")
    button(d, [1348, 130, 1416, 162], "검색", "primary", 13)
    d.rounded_rectangle([244, 188, 1416, 880], R, fill=CARD, outline=LINE)
    cols = [(264, "ID"), (380, "프로모션명"), (700, "유형"), (800, "기간"), (1040, "채널"), (1170, "상태"), (1260, "거래액"), (1360, "")]
    d.rectangle([245, 189, 1415, 229], fill="#F8F9FB")
    d.line([245, 229, 1415, 229], fill=LINE)
    for cx, h in cols:
        d.text((cx, 200), h, font=f(14), fill=MUTED)
    rows = [
        ("PROMO-26-021", "6월 첫 구매 웰컴 쿠폰", "쿠폰", "06-01 ~ 06-30", "자사몰", "예정", "-"),
        ("PROMO-26-019", "썸머 클리어런스: 최대 60%", "기획전", "06-22 ~ 07-05", "자사몰 외 2", "예정", "-"),
        ("PROMO-26-018", "가정의 달 선물 기획전", "기획전", "04-20 ~ 05-10", "자사몰 외 1", "종료", "2.71억"),
        ("PROMO-26-016", "데일리핏 PB 2+1", "묶음할인", "05-04 ~ 05-31", "자사몰", "진행중", "8,420만"),
        ("PROMO-26-015", "앱 전용 주말 타임딜", "타임딜", "05-16 ~ 05-17", "자사몰 앱", "진행중", "1,930만"),
        ("PROMO-26-014", "리뷰 작성 적립금 2배", "적립", "05-01 ~ 05-31", "자사몰", "진행중", "-"),
        ("PROMO-26-012", "봄 아우터 라이브 특가", "라이브", "04-09 20:00", "라이브", "종료", "6,110만"),
        ("PROMO-26-007", "봄 신상 위크: 첫 봄옷 20%", "기획전", "03-09 ~ 03-22", "자사몰 외 2", "종료", "3.38억"),
        ("PROMO-26-022", "(복사) 썸머 클리어런스", "기획전", "미정", "-", "임시저장", "-"),
        ("PROMO-26-023", "7월 카드사 즉시할인", "카드할인", "07-01 ~ 07-15", "자사몰", "임시저장", "-"),
    ]
    for r, row in enumerate(rows):
        y = 229 + r * 58
        d.line([245, y + 58, 1415, y + 58], fill=LINE)
        for (cx, _), v in zip(cols[:5], row[:5]):
            color = MUTED if cx in (264, 800) else TXT
            d.text((cx, y + 20), v, font=f(13 if cx == 264 else 15), fill=color)
        badge(d, 1170, y + 17, row[5])
        text_r(d, 1340, y + 20, row[6], 15, TXT if row[6] != "-" else MUTED)
        for k in range(3):  # "more" menu dots
            d.ellipse([1372 + k * 8, y + 27, 1376 + k * 8, y + 31], fill=MUTED)
    py = 836
    for i, p in enumerate(["<", "1", "2", "3", ">"]):
        x = 720 + i * 40
        on = p == "1"
        d.rounded_rectangle([x, py, x + 32, py + 32], 6, fill=PRIMARY if on else CARD, outline=None if on else LINE)
        text_c(d, [x, py, x + 32, py + 32], p, 14, "white" if on else TXT)
    im.save(OUT / "03-promotion-list.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    product_list()
    product_register()
    promotion_list()
    print("wrote 3 admin screens to", OUT)
