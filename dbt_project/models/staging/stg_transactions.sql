with source as (
    select * from {{ source('raw', 'train_transactions') }}
),

renamed as (
    select
        "TransactionID"::bigint                                    as transaction_id,
        "isFraud"::integer                                         as is_fraud,
        (timestamp '2017-12-01 00:00:00'
            + ("TransactionDT"::numeric * interval '1 second'))    as transaction_at,
        "TransactionAmt"::numeric                                  as amount,
        "ProductCD"                                                as product_code,
        "card1"::text                                              as card1,
        "card2"::text                                              as card2,
        "card3"::text                                              as card3,
        "card5"::text                                              as card5,
        "addr1"::text                                              as addr1,
        "addr2"::text                                              as addr2,
        "P_emaildomain"                                            as purchaser_email_domain,
        "R_emaildomain"                                            as recipient_email_domain
    from source
)

select * from renamed
