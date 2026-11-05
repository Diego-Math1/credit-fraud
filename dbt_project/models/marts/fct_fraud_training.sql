{{ config(materialized='table') }}

with features as (
    select * from {{ ref('int_transaction_features') }}
),

labels as (
    select
        transaction_id,
        is_fraud,
        product_code,
        purchaser_email_domain,
        recipient_email_domain
    from {{ ref('stg_transactions') }}
),

joined as (
    select
        f.transaction_id,
        f.transaction_at,
        f.customer_key,
        f.amount,

        -- velocity
        f.txn_count_1h,  f.amount_sum_1h,  f.amount_avg_1h,
        f.txn_count_24h, f.amount_sum_24h, f.amount_avg_24h,
        f.txn_count_7d,  f.amount_sum_7d,  f.amount_avg_7d,

        -- deviation
        f.amount_avg_last30,
        f.amount_std_last30,
        f.amount_deviation_ratio,
        f.amount_zscore_last30,

        -- recency
        f.seconds_since_prev_txn,

        -- target + categóricas (mantidas como texto; o encoder fica no Python)
        l.is_fraud,
        l.product_code,
        l.purchaser_email_domain,
        l.recipient_email_domain

    from features f
    left join labels l using (transaction_id)
),

with_split as (
    select
        *,
        case
            when percent_rank() over (order by transaction_at) <= 0.70 then 'train'
            when percent_rank() over (order by transaction_at) <= 0.85 then 'val'
            else 'test'
        end as split
    from joined
)

select * from with_split
