-- Invariante: janelas menores são subconjunto das maiores.
-- Se isso falhar, a lógica de janelas está errada.
select *
from {{ ref('int_transaction_features') }}
where txn_count_1h  > txn_count_24h
   or txn_count_24h > txn_count_7d
   or amount_sum_1h  > amount_sum_24h
   or amount_sum_24h > amount_sum_7d
