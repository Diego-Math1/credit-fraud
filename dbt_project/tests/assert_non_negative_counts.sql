select *
from {{ ref('int_transaction_features') }}
where txn_count_1h  < 0
   or txn_count_24h < 0
   or txn_count_7d  < 0
   or amount_sum_1h  < 0
   or amount_sum_24h < 0
   or amount_sum_7d  < 0
