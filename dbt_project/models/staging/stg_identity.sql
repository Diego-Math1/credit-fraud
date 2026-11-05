with source as (
    select * from {{ source('raw', 'train_identity') }}
),

renamed as (
    select
        "TransactionID"::bigint     as transaction_id,
        "DeviceType"                as device_type,
        "DeviceInfo"                as device_info,
        "id_30"                     as os,
        "id_31"                     as browser,
        "id_33"                     as screen_resolution
    from source
)

select * from renamed
