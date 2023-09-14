use std::fs::File;
use std::thread;
use std::time;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Event {
    remotehost: String,
    rfc931: String,
    authuser: String,
    pub date: u64,
    request: String,
    status: String,
    bytes: usize,
}

pub struct AccessLogAggregate {
    bucket_size_seconds: u64,
    bucket: u64,
    latest_time_before_close: u64,
    bytes: usize,
    is_closed: bool,
}

impl AccessLogAggregate {
    pub fn new(
        mut bucket_size_seconds: u64,
        bucket: u64,
        event: Option<&Event>,
    ) -> AccessLogAggregate {
        let mut bytes = 0;
        if let Some(_event) = &event {
            bucket_size_seconds = 0;
            bytes = _event.bytes;
        };
        AccessLogAggregate {
            bucket_size_seconds,
            bucket,
            latest_time_before_close: bucket + bucket_size_seconds + 30,
            bytes,
            is_closed: false,
        }
    }
}

struct AccessLogMonitor {
    window_size_seconds: u64,
    min_window_size_seconds: u64,
    first_event_timestamp: u64,
    last_event_timestamp: u64,
    alert_threshold: u64,
    alert_triggered: bool,
    times_alert_triggered: u64,
    window: Box<Vec<Event>>,
}

impl AccessLogMonitor {
    pub fn new() -> AccessLogMonitor {
        AccessLogMonitor {
            window_size_seconds: 0,
            min_window_size_seconds: 0,
            first_event_timestamp: 0,
            last_event_timestamp: 0,
            alert_threshold: 0,
            alert_triggered: false,
            times_alert_triggered: 0,
            window: Box::new(Vec::new()),
        }
    }

    pub fn check(&self, aggregate: &AccessLogAggregate) {}
}

fn update(aggregate: &AccessLogAggregate) {}

pub fn process(reader: &mut csv::Reader<File>, timescale: f32) {
    let monitor = AccessLogMonitor::new();
    let mut current_timestamp: u64 = 0;
    for result in reader.deserialize::<Event>() {
        if let Err(why) = result {
            println!("Encountered malformed log line: {}", why);
        } else if let Ok(event) = result {
            let aggregate = process_event(&event, timescale, current_timestamp);
            current_timestamp = event.date;
            update(&aggregate);
            monitor.check(&aggregate);
        }
    }
}

fn process_event(event: &Event, timescale: f32, current_timestamp: u64) -> AccessLogAggregate {
    println!("{:?}", event);
    let wait_dur: u64;
    match current_timestamp {
        0 => wait_dur = 0,
        _ => {
            wait_dur =
                (timescale * 1000_f32 * event.date.saturating_sub(current_timestamp) as f32) as u64;
        }
    }
    thread::sleep(time::Duration::from_millis(wait_dur));
    AccessLogAggregate::new(0, current_timestamp, Some(&event))
}
