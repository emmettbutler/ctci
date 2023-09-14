use std::error::Error;
use std::path::PathBuf;

use clap::Parser;
use csv;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Event {
    remotehost: String,
    rfc931: String,
    authuser: String,
    date: String,
    request: String,
    status: String,
    bytes: String,
}

#[derive(Debug, Parser)]
#[clap(author, version, about = "Monitor and analyze a CSV HTTP access log.")]
struct Cli {
    /// CSV file from which to read log
    #[clap(value_parser)]
    input_file: PathBuf,

    /// Average requests per second during the monitoring window above which to alert
    #[clap(short = 'a', long, value_parser, default_value_t = 10.0)]
    alert_threshold: f32,

    /// The size in seconds of the rolling window over which alerts are evaluated
    #[clap(short = 'w', long, value_parser, default_value_t = 120)]
    alert_window: i32,

    /// The size in seconds of the aggregation buckets in which alerts are analyzed
    #[clap(short = 'b', long, value_parser, default_value_t = 10)]
    analysis_bucket_size: i32,

    /// How fast events should play back. Set between 0 and 1 for faster playback, above 1 for slower.
    /// Defaults to 0 (no playback delay)
    #[clap(short = 't', long, value_parser, default_value_t = 0.0)]
    timescale: f32,

    /// Enable verbose logging
    #[clap(short, long, action = clap::ArgAction::Count)]
    verbose: u8,
}

fn read_access_log(input_file: PathBuf, timescale: f32) -> Result<(), Box<dyn Error>> {
    let mut reader = csv::Reader::from_path(input_file)?;
    for result in reader.deserialize::<Event>() {
        match result {
            Ok(value) => println!("{:?}", value),
            Err(_) => continue,
        };
    }
    Ok(())
}

fn main() {
    let cli = Cli::parse();
    match read_access_log(cli.input_file, cli.timescale) {
        Ok(_) => println!("success"),
        Err(e) => println!("{}", e),
    };
}
