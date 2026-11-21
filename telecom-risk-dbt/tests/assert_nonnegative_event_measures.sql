select subscriber_id, event_date
from {{ ref('int_subscriber_daily') }}
where event_count < 0
   or total_duration_seconds < 0
   or total_amount < 0
