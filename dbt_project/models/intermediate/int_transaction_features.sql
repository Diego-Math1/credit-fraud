{{ config(materialized='table') }}

with base as (
    select
        transaction_id,
        transaction_at,
        amount,
        coalesce(nullif(card1, ''), 'NA') || '|' ||
        coalesce(nullif(card2, ''), 'NA') || '|' ||
        coalesce(nullif(card3, ''), 'NA') || '|' ||
        coalesce(nullif(card5, ''), 'NA') || '|' ||
        coalesce(nullif(addr1, ''), 'NA') as customer_key
    from {{ ref('stg_transactions') }}
),

windowed as (
    select
        transaction_id,
        transaction_at,
        customer_key,
        amount,

        -- VELOCITY (1h / 24h / 7d) — EXCLUDE CURRENT ROW = anti-leakage
        count(*)             over w_1h  as txn_count_1h,
        coalesce(sum(amount) over w_1h, 0) as amount_sum_1h,
        avg(amount)          over w_1h  as amount_avg_1h,

        count(*)             over w_24h as txn_count_24h,
        coalesce(sum(amount) over w_24h, 0) as amount_sum_24h,
        avg(amount)          over w_24h as amount_avg_24h,

        count(*)             over w_7d  as txn_count_7d,
        coalesce(sum(amount) over w_7d, 0) as amount_sum_7d,
        avg(amount)          over w_7d  as amount_avg_7d,

        -- DEVIATION (últimas 30 transações do cliente)
        avg(amount)    over w_30rows as amount_avg_last30,
        stddev(amount) over w_30rows as amount_std_last30,

        -- RECENCY
        lag(transaction_at) over (
            partition by customer_key
            order by transaction_at, transaction_id
        ) as prev_txn_at

    from base
    window
        w_1h  as (
            partition by customer_key
            order by transaction_at
            range between interval '1 hour' preceding and current row
            exclude current row
        ),
        w_24h as (
            partition by customer_key
            order by transaction_at
            range between interval '24 hours' preceding and current row
            exclude current row
        ),
        w_7d  as (
            partition by customer_key
            order by transaction_at
            range between interval '7 days' preceding and current row
            exclude current row
        ),
        w_30rows as (
            partition by customer_key
            order by transaction_at, transaction_id
            rows between 30 preceding and 1 preceding
        )
)

select
    transaction_id,
    transaction_at,
    customer_key,
    amount,

    txn_count_1h,  amount_sum_1h,  amount_avg_1h,
    txn_count_24h, amount_sum_24h, amount_avg_24h,
    txn_count_7d,  amount_sum_7d,  amount_avg_7d,

    amount_avg_last30,
    amount_std_last30,
    case when amount_avg_last30 > 0
         then amount / amount_avg_last30
         else null
    end as amount_deviation_ratio,
    case when amount_std_last30 > 0
         then (amount - amount_avg_last30) / amount_std_last30
         else null
    end as amount_zscore_last30,

    extract(epoch from (transaction_at - prev_txn_at)) as seconds_since_prev_txn

from windowed
