use std::error::Error;
use std::path::PathBuf;
use std::thread;
use std::time;

use csv;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Event {
    remotehost: String,
    rfc931: String,
    authuser: String,
    date: u64,
    request: String,
    status: String,
    bytes: usize,
}

struct AccessLogAggregate {
    bucket_size_seconds: u32,
    bucket: u32,
    latest_time_before_close: u32,
    bytes: usize,
    is_closed: bool,
}

impl AccessLogAggregate {
    pub fn new(
        mut bucket_size_seconds: u32,
        bucket: u32,
        event: Option<Event>,
    ) -> AccessLogAggregate {
        let mut bytes = 0;
        if let Some(_event) = event {
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

pub fn read_access_log(input_file: PathBuf, timescale: f32) -> Result<(), Box<dyn Error>> {
    let mut current_timestamp: u64 = 0;
    let mut reader = csv::Reader::from_path(input_file)?;
    for result in reader.deserialize::<Event>() {
        match result {
            Err(why) => {
                println!("Malformed log entry encountered: {}", why);
                continue;
            }
            Ok(event) => {
                println!("{:?}", event);
                let wait_dur: u64;
                match current_timestamp {
                    0 => wait_dur = 0,
                    _ => {
                        wait_dur = (timescale
                            * 1000_f32
                            * event.date.saturating_sub(current_timestamp) as f32)
                            as u64;
                    }
                }
                thread::sleep(time::Duration::from_millis(wait_dur));
                current_timestamp = event.date;
            }
        };
    }
    Ok(())
}
