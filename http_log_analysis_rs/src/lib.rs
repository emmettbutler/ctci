use std::cmp;
use std::collections::HashMap;
use std::fs::File;
use std::rc::Rc;
use std::thread;
use std::time;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Event {
    remotehost: String,
    rfc931: String,
    authuser: String,
    date: i32,
    request: String,
    status: String,
    bytes: usize,
}

#[derive(Debug)]
struct AccessLogAggregate {
    bucket_size_seconds: i32,
    bucket: i32,
    latest_time_before_close: i32,
    bytes: usize,
    is_closed: bool,
}

impl AccessLogAggregate {
    /// Create an aggregate over a time-grouping of other AccessLogAggregates
    ///
    /// An AccessLogAggregate can represent one or more log events. When it represents only one event,
    /// self.bucket_size_seconds is 0.
    ///
    /// # Arguments
    ///
    /// * `bucket_size_seconds` - The size of the time bucket represented by this aggregate
    /// * `bucket` - The epoch timestamp of the beginning of the time bucket represented by this aggregate
    /// * `event` - An event that, if given, initializes analysis counters for the aggregate
    ///
    fn new(mut bucket_size_seconds: i32, bucket: i32, event: Option<&Event>) -> AccessLogAggregate {
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

    /// Update analysis counters with information from the given aggregate
    fn add(&mut self, aggregate: &AccessLogAggregate) {
        if self.is_closed {
            return;
        }
        self.bytes += aggregate.bytes;
    }

    /// Mark this aggregate as closed and log its collected stats
    fn close(&mut self) {
        // XXX print more stats computation here
        println!(
            "Bucket={}\n\tBucket size={}\n\tBytes={}\n",
            self.bucket, self.bucket_size_seconds, self.bytes,
        );
        self.is_closed = true;
    }
}

struct AccessLogMonitor {
    window_size_seconds: i32,
    min_window_size_seconds: i32,
    first_event_timestamp: i32,
    last_event_timestamp: i32,
    alert_threshold: f32,
    alert_triggered: bool,
    times_alert_triggered: i32,
    window: Box<Vec<Rc<AccessLogAggregate>>>,
}

impl AccessLogMonitor {
    /// Create a monitor over AccessLogAggregates based on a sliding window
    ///
    /// # Arguments
    ///
    /// * `window_size_seconds` - The size of the sliding window used for analysis, in seconds
    /// * `threshold` - The number of events per second on average over the monitoring window that will cause an alert
    fn new(window_size_seconds: i32, threshold: f32) -> AccessLogMonitor {
        AccessLogMonitor {
            window_size_seconds: 1,
            min_window_size_seconds: window_size_seconds,
            first_event_timestamp: 0,
            last_event_timestamp: 0,
            alert_threshold: threshold,
            alert_triggered: false,
            times_alert_triggered: 0,
            window: Box::new(Vec::new()),
        }
    }

    fn update(&mut self, aggregate: Rc<AccessLogAggregate>) {
        self.update_window(Rc::clone(&aggregate));
        if self.window_size_seconds >= self.min_window_size_seconds {
            self.evaluate_alert_conditions((&aggregate).bucket);
        }
    }

    /// Add the given event to the analysis window
    ///
    /// Maintains a sliding window by expelling old events as new ones are added
    /// Tracks the size of the window in seconds
    fn update_window(&mut self, event: Rc<AccessLogAggregate>) {
        self.window
            .retain(|e| e.bucket >= event.bucket - self.min_window_size_seconds);
        self.window.push(Rc::clone(&event));
        self.first_event_timestamp = cmp::min(self.window[0].bucket, event.bucket);
        self.last_event_timestamp =
            cmp::max(self.window[self.window.len() - 1].bucket, event.bucket);
        self.window_size_seconds = self.last_event_timestamp - self.first_event_timestamp;
    }

    /// Check the alert conditions and trigger alerts if applicable
    ///
    /// # Arguments
    ///
    /// * `timestamp` - The current time
    fn evaluate_alert_conditions(&mut self, timestamp: i32) {
        let mut average_events_per_second: f32 =
            self.window.len() as f32 / self.window_size_seconds as f32;
        average_events_per_second = (10.0 * average_events_per_second).round() / 10.0;
        if average_events_per_second > self.alert_threshold {
            self.trigger_alert(average_events_per_second, timestamp);
        } else {
            self.resolve_alert(average_events_per_second, timestamp);
        }
    }

    fn trigger_alert(&mut self, average_events_per_second: f32, current_time: i32) {
        if !self.alert_triggered {
            self.alert_triggered = true;
            self.times_alert_triggered += 1;
            println!(
                "High traffic generated an alert - hits = {}/s, triggered at {}\n",
                average_events_per_second, current_time,
            );
            println!(
                "window_size={}\n\tTotal events={}\n\tavg_events_per_second={}\n\tMore than {} events per second\n",
                self.window_size_seconds,
                self.window.len(),
                average_events_per_second,
                self.alert_threshold,
            );
        }
    }

    fn resolve_alert(&mut self, average_events_per_second: f32, current_time: i32) {
        if self.alert_triggered {
            self.alert_triggered = false;
            println!(
                "Reduced traffic resolved an alert - hits = {}/s, resolved at {}\n",
                average_events_per_second, current_time,
            );
        }
    }
}

/// Collect and report statistics on time-bucketed aggregates over the <aggregates> generator
///
/// This is a bare function as opposed to a class method because it doesn't have enough state to track
/// to warrant the extra level of encapsulation.
///
/// # Arguments
///
/// * `aggregates` - The sequence over which to aggregate
/// * `bucket_size_seconds` - The size in seconds of the aggregation buckets to analyze
fn update_stats(
    agg: &AccessLogAggregate,
    all_aggregates: &mut HashMap<i32, Box<AccessLogAggregate>>,
    bucket_size_seconds: i32,
) {
    let bucket = agg.bucket - agg.bucket % bucket_size_seconds;
    if !all_aggregates.contains_key(&bucket) {
        all_aggregates.insert(
            bucket,
            Box::new(AccessLogAggregate::new(bucket_size_seconds, bucket, None)),
        );
    }
    all_aggregates.get_mut(&bucket).unwrap().add(agg);

    for (_bucket, aggregate) in all_aggregates {
        if !aggregate.is_closed
            && agg.bucket > aggregate.latest_time_before_close
            && aggregate.bucket_size_seconds != 0
        {
            aggregate.close();
        }
    }
}

/// Generates AccessLogAggregates from a CSV reader
pub fn process(
    reader: &mut csv::Reader<File>,
    timescale: f32,
    bucket_size_seconds: i32,
    alert_window: i32,
    alert_threshold: f32,
) {
    let mut monitor = AccessLogMonitor::new(alert_window, alert_threshold);
    let mut all_aggregates: HashMap<i32, Box<AccessLogAggregate>> = HashMap::new();
    let mut current_timestamp: i32 = 0;
    for result in reader.deserialize::<Event>() {
        if let Err(why) = result {
            println!("Encountered malformed log line: {}", why);
        } else if let Ok(event) = result {
            let aggregate = process_event(&event, timescale, current_timestamp);
            current_timestamp = event.date;
            update_stats(&aggregate, &mut all_aggregates, bucket_size_seconds);
            all_aggregates = all_aggregates
                .into_iter()
                .filter(|(_, agg)| !agg.is_closed)
                .collect();
            monitor.update(Rc::new(aggregate));
        }
    }
}

/// Build an `AccessLogAggregate` from the given `Event`
///
/// Simulates delayed event arrival with time.sleep.
///
/// # Arguments
///
/// * `timescale` - A multiplier applied to the sleep time between events. The sleep time defaults to the difference
///    between the each pair of event timestamps in the log.
/// * `current_timestamp` - The timestamp of the previously processed event
fn process_event(event: &Event, timescale: f32, current_timestamp: i32) -> AccessLogAggregate {
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
