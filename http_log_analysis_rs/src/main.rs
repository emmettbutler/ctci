use std::path::PathBuf;

use clap::Parser;

use http_log_analysis_rs;

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

fn main() {
    let cli = Cli::parse();
    let reader = csv::Reader::from_path(cli.input_file);
    match reader {
        Err(why) => panic!("Failed to create CSV reader: {}", why),
        Ok(mut _reader) => {
            http_log_analysis_rs::process(&mut _reader, cli.timescale, cli.analysis_bucket_size)
        }
    };
}
