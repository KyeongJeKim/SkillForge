#!/usr/bin/env python3
"""Regenerate the Office/Hangul test fixtures with the standard library only.

Writes:
  pos-specs-messy/FS-POS-12_거래보류.docx      (WordprocessingML, Heading1/2 + tables + bullets)
  pos-specs-messy/포인트적립_기능명세서.hwpx    (OWPML: mimetype, version.xml, container, hpf, header, section0)
  pm-qa-xlsx/QA_테스트케이스_간편재주문.xlsx   (SpreadsheetML, sharedStrings, 2 sheets)

Usage: python3 make_office_fixtures.py [fixtures_dir]   (default: this script's folder)
All names, numbers and companies are fictional.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
FIXED_TIME = (2026, 3, 9, 10, 0, 0)  # stable zip timestamps so reruns produce identical files


def _write_zip(path: Path, parts: list[tuple[str, str | bytes]], stored_first: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        for i, (name, data) in enumerate(parts):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_STORED if (stored_first and i == 0) else zipfile.ZIP_DEFLATED
            z.writestr(info, data.encode("utf-8") if isinstance(data, str) else data)


XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

# --------------------------------------------------------------------------- DOCX
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

DOCX_CONTENT = [
    ("Heading1", "FS-POS-12 거래 보류 및 불러오기"),
    ("table", [["항목", "내용"],
               ["기능 ID", "FS-POS-12"],
               ["기능명", "거래 보류 / 보류 거래 불러오기"],
               ["작성자", "박지훈 (POS개발파트)"],
               ["버전", "v1.1"],
               ["관련 화면", "SCR-SALE-01 판매, SCR-SALE-04 보류 목록"],
               ["상태", "확정"]]),
    ("Heading2", "1. 개요"),
    ("Normal", "결제 전 장바구니를 임시로 보류하고 다음 고객을 먼저 응대한 뒤, 보류한 거래를 다시 불러와 결제를 이어간다."),
    ("Normal", "보류 거래는 단말기 로컬 DB에 저장되며 영업 마감 시 자동 삭제된다."),
    ("Heading2", "2. 화면"),
    ("bullet", "판매 화면(SCR-SALE-01) 우측 하단 [보류] 버튼, 장바구니가 비어 있으면 비활성"),
    ("bullet", "보류 시 메모 입력 팝업(선택): 예) \"창가 테이블\", \"포장 대기\""),
    ("bullet", "판매 화면 상단 [보류 n건] 배지 → 보류 목록(SCR-SALE-04)"),
    ("bullet", "보류 목록: 보류 시각, 메모, 품목 수, 합계 금액, [불러오기] [삭제]"),
    ("Heading2", "3. 기능 상세"),
    ("table", [["No", "요구사항", "처리 규칙", "우선순위"],
               ["FS-POS-12-01", "거래 보류", "현재 장바구니 전체를 보류 목록에 저장하고 장바구니 초기화", "필수"],
               ["FS-POS-12-02", "보류 한도", "단말기당 최대 5건, 초과 시 보류 불가", "필수"],
               ["FS-POS-12-03", "불러오기", "현재 장바구니가 비어 있을 때만 가능, 불러온 건은 목록에서 제거", "필수"],
               ["FS-POS-12-04", "가격 재계산", "불러올 때 현재 판매가·프로모션 기준으로 재계산하고 변경 품목 표시", "필수"],
               ["FS-POS-12-05", "자동 삭제", "영업 마감(정산) 시 미처리 보류 건 삭제, 삭제 내역 로그 저장", "필수"],
               ["FS-POS-12-06", "메모", "최대 20자, 이모지 입력 불가", "선택"]]),
    ("Heading2", "4. 입력/출력"),
    ("table", [["구분", "항목", "형식", "비고"],
               ["입력", "장바구니", "품목 배열(상품코드, 수량, 단가)", "판매 화면에서 전달"],
               ["입력", "메모", "문자열 20자 이내", "선택 입력"],
               ["출력", "보류 레코드", "hold_id, 보류시각, 캐셔ID, 품목, 합계", "로컬 DB 저장"],
               ["출력", "보류 배지 수", "정수 0~5", "판매 화면 상단"]]),
    ("Heading2", "5. 예외 처리"),
    ("table", [["상황", "메시지", "처리"],
               ["보류 5건 초과", "보류할 수 있는 거래는 최대 5건입니다.", "보류 목록 바로가기 제공"],
               ["장바구니가 비어 있지 않은 상태에서 불러오기", "진행 중인 거래를 먼저 결제하거나 보류해 주세요.", "불러오기 취소"],
               ["불러온 거래에 판매 중지 상품 포함", "판매가 중지된 상품 1개를 제외했습니다.", "해당 품목 제외 후 불러오기"],
               ["단말기 재시작", "-", "로컬 DB에서 보류 목록 복원"]]),
    ("Heading2", "6. 권한"),
    ("table", [["역할", "보류", "불러오기", "보류 건 삭제"],
               ["캐셔", "O", "O (본인 보류 건)", "X"],
               ["매니저", "O", "O (전체)", "O"]]),
    ("Heading2", "7. 변경 이력"),
    ("table", [["버전", "날짜", "작성자", "내용"],
               ["v1.0", "2025-11-10", "박지훈", "최초 작성"],
               ["v1.1", "2026-01-08", "박지훈", "가격 재계산 규칙, 메모 20자 제한 추가"]]),
    ("Heading3", "참고"),
    ("Normal", "보류 건 서버 동기화(다른 단말기에서 불러오기)는 2차 범위. 관련 이슈 POS-JIRA-512 (가상)."),
]


def _w_run(text: str, bold: bool = False) -> str:
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def _w_para(style: str, text: str) -> str:
    if style == "bullet":
        ppr = '<w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>'
    elif style == "Normal":
        ppr = ""
    else:
        ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    return f"<w:p>{ppr}{_w_run(text)}</w:p>"


def _w_table(rows: list[list[str]]) -> str:
    ncol = len(rows[0])
    width = 9000 // ncol
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for _ in range(ncol))
    out = [f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="9000" w:type="dxa"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    for r, row in enumerate(rows):
        out.append("<w:tr>")
        for cell in row:
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>' if r == 0 else ""
            out.append(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr>'
                       f"<w:p>{_w_run(cell, bold=(r == 0))}</w:p></w:tc>")
        out.append("</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def build_docx(path: Path) -> None:
    body = []
    for kind, data in DOCX_CONTENT:
        if kind == "table":
            body.append(_w_table(data))
            body.append("<w:p/>")
        else:
            body.append(_w_para(kind, data))
    body.append('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="851" w:footer="992" w:gutter="0"/></w:sectPr>')
    document = (XML_DECL + f'<w:document xmlns:w="{W_NS}" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f"<w:body>{''.join(body)}</w:body></w:document>")

    def style(sid: str, name: str, size: int, bold: bool, based: str = "Normal", outline: int | None = None) -> str:
        ppr = f'<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="{outline}"/></w:pPr>' if outline is not None else ""
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/><w:basedOn w:val="{based}"/>'
                f'<w:next w:val="Normal"/><w:qFormat/>{ppr}<w:rPr>{"<w:b/>" if bold else ""}<w:sz w:val="{size}"/></w:rPr></w:style>')

    styles = (XML_DECL + f'<w:styles xmlns:w="{W_NS}">'
              '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Malgun Gothic" w:eastAsia="맑은 고딕" w:hAnsi="Malgun Gothic"/>'
              '<w:sz w:val="20"/><w:lang w:val="en-US" w:eastAsia="ko-KR"/></w:rPr></w:rPrDefault>'
              '<w:pPrDefault><w:pPr><w:spacing w:after="80" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
              + style("Title", "Title", 36, True)
              + style("Heading1", "heading 1", 28, True, outline=0)
              + style("Heading2", "heading 2", 24, True, outline=1)
              + style("Heading3", "heading 3", 22, True, outline=2)
              + '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/>'
                '<w:pPr><w:ind w:left="800"/></w:pPr></w:style>'
              '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/>'
              '<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'
              '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:basedOn w:val="TableNormal"/><w:tblPr><w:tblBorders>'
              + "".join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="808080"/>' for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
              + "</w:tblBorders></w:tblPr></w:style></w:styles>")
    numbering = (XML_DECL + f'<w:numbering xmlns:w="{W_NS}"><w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>'
                 '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
                 '<w:pPr><w:ind w:left="800" w:hanging="400"/></w:pPr></w:lvl></w:abstractNum>'
                 '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>')
    content_types = (XML_DECL + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                     '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                     '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                     '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
                     "</Types>")
    rels = (XML_DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            "</Relationships>")
    doc_rels = (XML_DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
                "</Relationships>")
    core = (XML_DECL + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            "<dc:title>FS-POS-12 거래 보류 및 불러오기</dc:title><dc:creator>박지훈</dc:creator><cp:lastModifiedBy>박지훈</cp:lastModifiedBy>"
            '<dcterms:created xsi:type="dcterms:W3CDTF">2025-11-10T09:00:00Z</dcterms:created>'
            '<dcterms:modified xsi:type="dcterms:W3CDTF">2026-01-08T17:20:00Z</dcterms:modified></cp:coreProperties>')
    app = (XML_DECL + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           "<Application>Microsoft Office Word</Application><Company>데모POS</Company></Properties>")
    _write_zip(path, [("[Content_Types].xml", content_types), ("_rels/.rels", rels),
                      ("word/document.xml", document), ("word/styles.xml", styles),
                      ("word/numbering.xml", numbering), ("word/_rels/document.xml.rels", doc_rels),
                      ("docProps/core.xml", core), ("docProps/app.xml", app)])


# --------------------------------------------------------------------------- HWPX
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HS = "http://www.hancom.co.kr/hwpml/2011/section"
HH = "http://www.hancom.co.kr/hwpml/2011/head"

# No 기능 ID anywhere: this is the "missing ID" spec of the set.
HWPX_CONTENT = [
    ("h", "포인트 적립/사용 기능명세서"),
    ("table", [["항목", "내용"],
               ["기능명", "회원 포인트 적립 및 사용"],
               ["작성자", "최유진 (POS기획)"],
               ["버전", "1.0"],
               ["관련 화면", "SCR-PAY-01 결제, SCR-MEM-01 회원 조회"],
               ["상태", "검토 요청"]]),
    ("h", "1. 개요"),
    ("p", "결제 시 회원을 조회하여 결제 금액의 일정 비율을 포인트로 적립하거나, 보유 포인트를 결제 수단으로 사용한다."),
    ("p", "포인트 정책(적립률, 최소 사용 단위)은 본사 관리자 화면에서 설정하며 POS는 개점 시 정책을 내려받는다."),
    ("h", "2. 화면"),
    ("p", "- 결제 화면 [회원] 버튼 → 회원 조회 팝업(휴대폰 뒷 4자리 또는 바코드)"),
    ("p", "- 회원 선택 시 결제 화면 상단에 회원명(마스킹), 등급, 보유 포인트 표시"),
    ("p", "- [포인트 사용] 버튼 → 사용 금액 입력 키패드, [전액 사용] 버튼"),
    ("h", "3. 기능 상세"),
    ("table", [["No", "요구사항", "처리 규칙", "우선순위"],
               ["01", "기본 적립", "실결제 금액(포인트 사용분 제외)의 1%, 원 단위 절사", "필수"],
               ["02", "등급 적립", "VIP 2%, 골드 1.5% (정책 서버 기준)", "필수"],
               ["03", "사용 단위", "1,000P 이상 100P 단위 사용", "필수"],
               ["04", "적립 시점", "결제 완료 즉시 가적립, 7일 후 확정", "필수"],
               ["05", "환불", "환불 시 적립 포인트 회수, 사용 포인트 복원", "필수"]]),
    ("h", "4. 입력/출력"),
    ("table", [["구분", "항목", "형식", "비고"],
               ["입력", "회원 식별값", "휴대폰 뒷 4자리 / 회원 바코드", "복수 검색 시 목록 선택"],
               ["입력", "사용 포인트", "정수(P)", "100P 단위"],
               ["출력", "적립 예정 포인트", "정수(P)", "영수증 하단 인쇄"],
               ["출력", "포인트 거래 로그", "회원ID, 거래번호, 적립/사용, 금액", "서버 전송"]]),
    ("h", "5. 예외 처리"),
    ("table", [["상황", "메시지", "처리"],
               ["보유 포인트 부족", "사용 가능한 포인트는 {n}P 입니다.", "입력값 초기화"],
               ["포인트 서버 응답 없음", "포인트 서버에 연결할 수 없습니다. 적립은 나중에 처리됩니다.", "적립 대기열 저장, 사용 불가"],
               ["휴면 회원", "휴면 회원은 포인트를 사용할 수 없습니다.", "적립만 가능"]]),
    ("h", "6. 권한"),
    ("p", "- 캐셔: 적립, 사용"),
    ("p", "- 매니저: 수동 적립(영수증 지참 고객, 당일 거래 한정)"),
    ("h", "7. 변경 이력"),
    ("table", [["버전", "날짜", "작성자", "내용"],
               ["1.0", "2026.02.27", "최유진", "최초 작성 (기능 ID 부여 요청 중)"]]),
]


def _hp_para(text: str, char: int = 0, para: int = 0, style: int = 0) -> str:
    return (f'<hp:p id="0" paraPrIDRef="{para}" styleIDRef="{style}" pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{char}"><hp:t>{escape(text)}</hp:t></hp:run></hp:p>')


def _hp_table(rows: list[list[str]], tid: int) -> str:
    ncol, nrow = len(rows[0]), len(rows)
    cw, ch = 42520 // ncol, 1800
    out = [f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0">'
           f'<hp:tbl id="{tid}" zOrder="{tid}" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" '
           f'dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="{nrow}" colCnt="{ncol}" cellSpacing="0" borderFillIDRef="2" noAdjust="0">'
           f'<hp:sz width="{cw * ncol}" widthRelTo="ABSOLUTE" height="{ch * nrow}" heightRelTo="ABSOLUTE" protect="0"/>'
           '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" '
           'horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           '<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="510" right="510" top="141" bottom="141"/>']
    for r, row in enumerate(rows):
        out.append("<hp:tr>")
        for c, cell in enumerate(row):
            out.append(f'<hp:tc name="" header="{1 if r == 0 else 0}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="2">'
                       '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" '
                       'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
                       + _hp_para(cell, char=2 if r == 0 else 0)
                       + f'</hp:subList><hp:cellAddr colAddr="{c}" rowAddr="{r}"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
                       f'<hp:cellSz width="{cw}" height="{ch}"/><hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')
        out.append("</hp:tr>")
    out.append("</hp:tbl></hp:run></hp:p>")
    return "".join(out)


def build_hwpx(path: Path) -> None:
    body, plain, tid = [], [], 1000
    for kind, data in HWPX_CONTENT:
        if kind == "table":
            body.append(_hp_table(data, tid))
            tid += 1
            plain.extend("\t".join(r) for r in data)
        elif kind == "h":
            body.append(_hp_para(data, char=1, para=1, style=1))
            plain.append(data)
        else:
            body.append(_hp_para(data))
            plain.append(data)
    section = (XML_DECL + f'<hs:sec xmlns:hs="{HS}" xmlns:hp="{HP}" xmlns:hh="{HH}">' + "".join(body) + "</hs:sec>")
    version = (XML_DECL + '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" tagetApplication="WORDPROCESSOR" '
               'major="5" minor="1" micro="0" buildNumber="1" os="1" xmlVersion="1.4" application="Hancom Office Hangul" appVersion="12, 0, 0, 0"/>')
    container = (XML_DECL + '<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" '
                 'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"><ocf:rootfiles>'
                 '<ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>'
                 '<ocf:rootfile full-path="Preview/PrvText.txt" media-type="text/plain"/>'
                 "</ocf:rootfiles></ocf:container>")
    hpf = (XML_DECL + '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/" version="" unique-identifier="" id="">'
           "<opf:metadata><opf:title>포인트 적립/사용 기능명세서</opf:title><opf:language>ko</opf:language>"
           '<opf:meta name="creator" content="text">최유진</opf:meta>'
           '<opf:meta name="CreatedDate" content="text">2026-02-27T05:10:00Z</opf:meta></opf:metadata>'
           '<opf:manifest><opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>'
           '<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/></opf:manifest>'
           '<opf:spine><opf:itemref idref="header" linear="yes"/><opf:itemref idref="section0" linear="yes"/></opf:spine></opf:package>')

    def font(fid: int, name: str) -> str:
        return f'<hh:font id="{fid}" face="{name}" type="TTF" isEmbedded="0"/>'

    fontfaces = "".join(f'<hh:fontface lang="{lang}" fontCnt="2">{font(0, "함초롬바탕")}{font(1, "맑은 고딕")}</hh:fontface>'
                        for lang in ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER"))

    def char_pr(cid: int, height: int, bold: bool, face: int) -> str:
        ref = "".join(f'{k}="{face}"' + " " for k in ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user"))
        return (f'<hh:charPr id="{cid}" height="{height}" textColor="#000000" shadeColor="none" useFontSpace="0" useKerning="0" '
                f'symMark="NONE" borderFillIDRef="1"><hh:fontRef {ref}/>{"<hh:bold/>" if bold else ""}</hh:charPr>')

    header = (XML_DECL + f'<hh:head xmlns:hh="{HH}" xmlns:hp="{HP}" version="1.4" secCnt="1">'
              '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/><hh:refList>'
              f'<hh:fontfaces itemCnt="7">{fontfaces}</hh:fontfaces>'
              '<hh:borderFills itemCnt="2">'
              '<hh:borderFill id="1" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0"/>'
              '<hh:borderFill id="2" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
              '<hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/><hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>'
              '<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/><hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>'
              "</hh:borderFill></hh:borderFills>"
              '<hh:charProperties itemCnt="3">' + char_pr(0, 1000, False, 0) + char_pr(1, 1400, True, 1) + char_pr(2, 1000, True, 0) + "</hh:charProperties>"
              '<hh:paraProperties itemCnt="2">'
              '<hh:paraPr id="0" tabPrIDRef="0" condense="0"><hh:align horizontal="JUSTIFY" vertical="BASELINE"/>'
              '<hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/></hh:paraPr>'
              '<hh:paraPr id="1" tabPrIDRef="0" condense="0"><hh:align horizontal="LEFT" vertical="BASELINE"/>'
              '<hh:heading type="OUTLINE" idRef="0" level="0"/><hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/></hh:paraPr>'
              "</hh:paraProperties>"
              '<hh:styles itemCnt="2">'
              '<hh:style id="0" type="PARA" name="바탕글" engName="Normal" paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0" langID="1042" lockForm="0"/>'
              '<hh:style id="1" type="PARA" name="개요 1" engName="Outline 1" paraPrIDRef="1" charPrIDRef="1" nextStyleIDRef="0" langID="1042" lockForm="0"/>'
              "</hh:styles></hh:refList></hh:head>")
    preview = "\r\n".join(plain)[:1024]
    _write_zip(path, [("mimetype", "application/hwp+zip"), ("version.xml", version),
                      ("META-INF/container.xml", container), ("Contents/content.hpf", hpf),
                      ("Contents/header.xml", header), ("Contents/section0.xml", section),
                      ("Preview/PrvText.txt", preview)], stored_first=True)


# --------------------------------------------------------------------------- XLSX
S_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
QA_HEADER = ["TC ID", "요구사항 ID", "구분", "사전조건", "테스트 절차", "기대 결과", "우선순위", "결과", "비고"]

# REQ-10 and REQ-12 intentionally have no test case (traceability gap for tests).
QA_SHEET1 = [
    ["TC-001", "REQ-01", "UI", "로그인, 배송완료 주문 1건 보유", "1. 마이페이지 > 주문내역 진입\n2. 배송완료 주문 확인", "주문 카드 하단에 [다시 담기] 버튼 노출", "상", "Pass", ""],
    ["TC-002", "REQ-01", "UI", "로그인, 배송중 주문 1건 보유", "1. 주문내역 진입\n2. 배송중 주문 확인", "[다시 담기] 버튼 미노출", "중", "Pass", ""],
    ["TC-003", "REQ-02", "기능", "배송완료 주문(옵션 A, 수량 2)", "1. [다시 담기] 탭\n2. 장바구니 이동", "옵션 A, 수량 2로 장바구니에 추가", "상", "Pass", ""],
    ["TC-004", "REQ-02", "기능", "장바구니에 동일 상품·옵션 1개 존재", "1. 같은 주문에서 [다시 담기] 탭", "기존 행 수량 합산 (1+2=3), 행 중복 없음", "상", "Fail", "행이 2개로 중복 생성됨 → BUG-2031"],
    ["TC-005", "REQ-03", "기능", "주문 상품 3개 중 1개 옵션 품절", "1. [다시 담기] 탭", "품절 1개 제외 2개 추가, 토스트 \"품절 상품 1개를 제외했어요\"", "상", "Pass", ""],
    ["TC-006", "REQ-03", "기능", "주문 상품 전부 품절", "1. [다시 담기] 탭", "장바구니 추가 없음, 토스트 \"담을 수 있는 상품이 없어요\"", "중", "Pass", ""],
    ["TC-007", "REQ-04", "UI", "판매 종료 상품 주문", "1. 주문내역에서 해당 주문 확인", "[다시 담기] 버튼 비활성(회색), 탭 시 반응 없음", "중", "Pass", ""],
    ["TC-008", "REQ-05", "기능", "주문 당시가 39,200원, 현재가 41,000원", "1. [다시 담기] 탭\n2. 장바구니 확인", "현재가 41,000원 적용, \"가격이 변경된 상품이 있어요\" 안내", "상", "Pass", ""],
    ["TC-009", "REQ-05", "기능", "주문 당시 쿠폰 적용 주문", "1. [다시 담기] 탭", "쿠폰은 재적용되지 않음, 상품만 담김", "중", "N/A", "쿠폰 정책 확정 후 재작성"],
    ["TC-010", "REQ-06", "기능", "주문내역 편집 모드, 주문 3건 선택(상품 합 8개)", "1. [선택 상품 다시 담기] 탭", "8개 상품 일괄 추가", "상", "Pass", ""],
    ["TC-011", "REQ-06", "경계값", "상품 합 21개 선택", "1. [선택 상품 다시 담기] 탭", "\"한 번에 20개까지 담을 수 있어요\" 안내, 추가 안 됨", "중", "Pass", ""],
    ["TC-012", "REQ-08", "기능", "품절 옵션 상세 진입", "1. 옵션 선택 > [재입고 알림 신청] 탭", "신청 완료 토스트, 버튼이 [알림 신청됨]으로 변경", "상", "Pass", ""],
    ["TC-013", "REQ-08", "기능", "이미 알림 신청한 옵션", "1. [알림 신청됨] 탭", "신청 취소 확인 팝업 노출", "하", "Pass", ""],
    ["TC-014", "REQ-09", "기능", "알림 신청 옵션 재입고 처리(어드민)", "1. 어드민에서 재고 0→10 변경\n2. 알림톡 수신 확인", "24시간 이내 알림톡 1회 수신", "상", "Blocked", "알림톡 스테이징 발송 불가 (인프라 요청 중)"],
    ["TC-015", "REQ-11", "기능", "비로그인", "1. 주문 조회(비회원) 화면에서 [다시 담기] 탭", "로그인 화면 이동, 로그인 후 원래 화면 복귀", "중", "Pass", ""],
]
QA_SHEET2 = [
    ["TC-101", "REQ-07", "경계값", "장바구니 99개 보유", "1. 상품 2개 주문 [다시 담기] 탭", "1개만 추가, \"장바구니는 최대 100개까지 담을 수 있어요\"", "상", "Pass", ""],
    ["TC-102", "REQ-07", "경계값", "장바구니 100개 보유", "1. [다시 담기] 탭", "추가 없음, 같은 안내 문구", "중", "Pass", ""],
    ["TC-103", "REQ-02", "예외", "네트워크 끊김", "1. 비행기 모드 ON\n2. [다시 담기] 탭", "\"네트워크 연결을 확인해 주세요\" 토스트, 장바구니 변경 없음", "중", "Pass", ""],
    ["TC-104", "REQ-02", "예외", "[다시 담기] 연타(0.2초 간격 3회)", "1. 버튼 빠르게 3회 탭", "1회만 처리, 수량 중복 증가 없음", "상", "Fail", "수량 6으로 증가 → BUG-2035"],
    ["TC-105", "REQ-05", "예외", "주문 상품 옵션이 삭제됨(옵션 개편)", "1. [다시 담기] 탭", "해당 상품 제외, \"옵션이 변경된 상품은 상세에서 다시 선택해 주세요\"", "중", "미실행", ""],
    ["TC-106", "REQ-09", "예외", "알림 신청 후 회원 탈퇴", "1. 탈퇴 처리\n2. 재입고 처리", "알림톡 미발송, 신청 내역 삭제", "중", "미실행", "개인정보팀 확인 필요"],
    ["TC-107", "REQ-03", "회귀", "기존 장바구니 담기(상품 상세)", "1. 상품 상세에서 [장바구니] 탭", "기존 동작 동일 (영향 없음)", "상", "Pass", ""],
    ["TC-108", "REQ-01", "회귀", "주문내역 무한 스크롤 50건 이상", "1. 주문내역 스크롤", "버튼 렌더링으로 인한 스크롤 끊김 없음 (60fps 근접)", "하", "Pass", "iOS 15 기기만 확인"],
    ["TC-109", "REQ-11", "회귀", "앱 자동 로그인 만료", "1. 토큰 만료 상태로 [다시 담기] 탭", "로그인 화면 이동 후 원래 동작 이어서 수행", "중", "Pass", ""],
    ["TC-110", "REQ-06", "예외", "선택 주문 중 1건이 취소 주문", "1. 편집 모드에서 취소 주문 선택 시도", "취소 주문은 체크박스 비활성", "하", "Pass", ""],
]


def _col(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def build_xlsx(path: Path) -> None:
    strings: list[str] = []
    index: dict[str, int] = {}

    def sid(text: str) -> int:
        if text not in index:
            index[text] = len(strings)
            strings.append(text)
        return index[text]

    def sheet_xml(info_rows: list[list[str]], rows: list[list[str]]) -> str:
        widths = [9, 11, 8, 30, 36, 40, 8, 9, 30]
        cols = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths))
        out, r = [], 1
        for info in info_rows:
            cells = "".join(f'<c r="{_col(c)}{r}" t="s" s="3"><v>{sid(v)}</v></c>' for c, v in enumerate(info) if v)
            out.append(f'<row r="{r}">{cells}</row>')
            r += 1
        r += 1  # blank spacer row, as people leave in real sheets
        header_row = r
        cells = "".join(f'<c r="{_col(c)}{r}" t="s" s="1"><v>{sid(v)}</v></c>' for c, v in enumerate(QA_HEADER))
        out.append(f'<row r="{r}">{cells}</row>')
        for row in rows:
            r += 1
            cells = "".join(f'<c r="{_col(c)}{r}" t="s" s="2"><v>{sid(v)}</v></c>' for c, v in enumerate(row) if v != "")
            out.append(f'<row r="{r}">{cells}</row>')
        last = f"{_col(len(QA_HEADER) - 1)}{r}"
        return (XML_DECL + f'<worksheet xmlns="{S_NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f'<dimension ref="A1:{last}"/>'
                f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="{header_row}" topLeftCell="A{header_row + 1}" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
                f'<sheetFormatPr defaultRowHeight="16.5"/><cols>{cols}</cols><sheetData>{"".join(out)}</sheetData>'
                f'<autoFilter ref="A{header_row}:{last}"/></worksheet>')

    info = [["프로젝트", "한빛몰 앱 간편 재주문 (v5.3)", "", "작성자", "QA 송하늘"],
            ["테스트 기간", "2026-04-13 ~ 2026-04-17", "", "빌드", "5.3.0 (402)"]]
    sheet1 = sheet_xml(info, QA_SHEET1)
    sheet2 = sheet_xml([["예외·경계값·회귀 케이스", "", "", "최종 수정", "2026-04-16"]], QA_SHEET2)
    shared = (XML_DECL + f'<sst xmlns="{S_NS}" count="{len(strings)}" uniqueCount="{len(strings)}">'
              + "".join(f'<si><t xml:space="preserve">{escape(s)}</t></si>' for s in strings) + "</sst>")
    workbook = (XML_DECL + f'<workbook xmlns="{S_NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<bookViews><workbookView activeTab="0"/></bookViews><sheets>'
                '<sheet name="기능 테스트" sheetId="1" r:id="rId1"/><sheet name="예외·회귀" sheetId="2" r:id="rId2"/></sheets>'
                '<definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">\'기능 테스트\'!$A$4:$I$19</definedName>'
                '<definedName name="_xlnm._FilterDatabase" localSheetId="1" hidden="1">\'예외·회귀\'!$A$3:$I$13</definedName></definedNames></workbook>')
    wb_rels = (XML_DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
               '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
               '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
               '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
               "</Relationships>")
    styles = (XML_DECL + f'<styleSheet xmlns="{S_NS}">'
              '<fonts count="2"><font><sz val="10"/><name val="맑은 고딕"/><family val="3"/></font>'
              '<font><b/><sz val="10"/><name val="맑은 고딕"/><family val="3"/></font></fonts>'
              '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
              '<fill><patternFill patternType="solid"><fgColor rgb="FFD9E2F3"/><bgColor indexed="64"/></patternFill></fill></fills>'
              '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>'
              '<border><left style="thin"><color rgb="FF808080"/></left><right style="thin"><color rgb="FF808080"/></right>'
              '<top style="thin"><color rgb="FF808080"/></top><bottom style="thin"><color rgb="FF808080"/></bottom><diagonal/></border></borders>'
              '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
              '<cellXfs count="4"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
              '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
              '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
              '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
              '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
    content_types = (XML_DECL + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                     '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                     '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                     '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
                     '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                     "</Types>")
    rels = (XML_DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>")
    _write_zip(path, [("[Content_Types].xml", content_types), ("_rels/.rels", rels),
                      ("xl/workbook.xml", workbook), ("xl/_rels/workbook.xml.rels", wb_rels),
                      ("xl/worksheets/sheet1.xml", sheet1), ("xl/worksheets/sheet2.xml", sheet2),
                      ("xl/sharedStrings.xml", shared), ("xl/styles.xml", styles)])


if __name__ == "__main__":
    build_docx(ROOT / "pos-specs-messy" / "FS-POS-12_거래보류.docx")
    build_hwpx(ROOT / "pos-specs-messy" / "포인트적립_기능명세서.hwpx")
    build_xlsx(ROOT / "pm-qa-xlsx" / "QA_테스트케이스_간편재주문.xlsx")
    print("wrote docx, hwpx, xlsx under", ROOT)
