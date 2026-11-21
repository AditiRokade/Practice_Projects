select
    subscriber_id,
    event_date,
    count(*) as event_count,
    count(distinct event_type) as event_type_count,
    sum(duration_seconds) as total_duration_seconds,
    sum(amount) as total_amount,
    min(event_ts) as first_event_ts,
    max(event_ts) as last_event_ts
from {{ ref('stg_telecom_events') }}
group by subscriber_id, event_date
