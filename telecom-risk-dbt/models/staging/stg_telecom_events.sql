select
    cast(event_id as varchar) as event_id,
    cast(subscriber_id as varchar) as subscriber_id,
    cast(event_ts as timestamp) as event_ts,
    lower(trim(cast(event_type as varchar))) as event_type,
    cast(duration_seconds as integer) as duration_seconds,
    cast(amount as decimal(12, 2)) as amount,
    upper(trim(cast(country as varchar))) as country,
    cast(event_ts as date) as event_date
from {{ ref('telecom_events') }}
where nullif(trim(cast(event_id as varchar)), '') is not null
  and nullif(trim(cast(subscriber_id as varchar)), '') is not null
  and cast(event_ts as timestamp) is not null
