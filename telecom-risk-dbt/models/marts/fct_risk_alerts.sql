select
    subscriber_id,
    event_date,
    event_count,
    event_type_count,
    total_duration_seconds,
    total_amount,
    first_event_ts,
    last_event_ts,
    case
        when event_count >= 3 or (total_amount >= 75 and event_type_count >= 2) then 'HIGH'
        when total_amount >= 35 then 'MEDIUM'
        else 'LOW'
    end as risk_level,
    case
        when event_count >= 3 or (total_amount >= 75 and event_type_count >= 2) then 80
        when total_amount >= 35 then 50
        else 10
    end as heuristic_score
from {{ ref('int_subscriber_daily') }}
