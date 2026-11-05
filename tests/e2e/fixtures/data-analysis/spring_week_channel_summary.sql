/* ============================================================
 * 파일명   : spring_week_channel_summary.sql
 * 목적     : 봄 신상 위크(PROMO-26-007) 기간 일자·채널별 주문수/매출 집계
 * 작성자   : 윤재석 (데이터분석파트)
 * 작성일   : 2026-03-19
 * 원천     : dw.fact_order, dw.fact_order_item, dw.dim_channel
 * 결과     : daily_channel_sales.csv (일자, 채널, 주문수, 매출)
 * 변경이력 : 2026-03-19 윤재석 최초 작성
 *            2026-03-20 윤재석 내부 테스트 계정 제외 조건 추가
 * ============================================================ */

WITH
-- [1] 분석 기간 내 유효 주문 (취소·테스트·내부 계정 제외)
orders_base AS (
    SELECT
        o.order_id
        , o.order_dt
        , o.channel_cd
        , o.member_id
    FROM dw.fact_order AS o
    WHERE o.order_dt >= DATE '2026-03-09'
      AND o.order_dt <  DATE '2026-03-19'
      AND o.order_status_cd NOT IN ('CANCEL', 'TEST')
      AND o.is_internal_user = FALSE
),

-- [2] 주문별 결제 금액 (상품 금액 - 할인, 배송비 제외)
order_amount AS (
    SELECT
        i.order_id
        , SUM(i.sale_amt - i.discount_amt) AS pay_amt
    FROM dw.fact_order_item AS i
    INNER JOIN orders_base AS b
        ON b.order_id = i.order_id
    GROUP BY
        i.order_id
),

-- [3] 일자·채널별 집계
daily_sales AS (
    SELECT
        b.order_dt
        , c.channel_nm
        , COUNT(DISTINCT b.order_id) AS order_cnt
        , SUM(a.pay_amt)             AS sales_amt
    FROM orders_base AS b
    INNER JOIN order_amount AS a
        ON a.order_id = b.order_id
    LEFT JOIN dw.dim_channel AS c
        ON c.channel_cd = b.channel_cd
    GROUP BY
        b.order_dt
        , c.channel_nm
)

SELECT
    d.order_dt                                        AS 일자
    , d.channel_nm                                    AS 채널
    , d.order_cnt                                     AS 주문수
    , d.sales_amt                                     AS 매출
FROM daily_sales AS d
ORDER BY
    d.order_dt
    , CASE d.channel_nm
          WHEN '자사몰_앱' THEN 1
          WHEN '자사몰_웹' THEN 2
          ELSE 3
      END
;

-- 검증용 (커밋 전 주석 유지): 기간 합계가 대시보드 "행사 기간 매출"과 ±0.5% 이내인지 확인
-- SELECT SUM(order_cnt), SUM(sales_amt) FROM daily_sales;
