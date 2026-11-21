select subscriber_id, event_date
from {{ ref('int_subscriber_daily') }}
group by subscriber_id, event_date
having count(*) > 1
