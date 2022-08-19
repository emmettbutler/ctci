HTTP Logfile Analyzer
=====================

This is a tool that facilitates simple analysis on HTTP logfiles formatted as CSV. It also simulates real-time playback of the request log with a configurable timeout.

Run it with this command:

```sh
$ python3.10 main.py readme_sample_csv.txt --timescale 0.01
```

You can provide a different input file if you want. If you do, make sure it conforms to the same CSV schema as the txt file included here.

You can also adjust various analysis values at the CLI, including alert threshold and window size. Use this command for more details:

```sh
$ python3.10 main.py --help
```

This tool has no Python dependencies - it uses only the Python 3.10 standard library.

You can run the unit test suite with this command:

```sh
$ python3.10 tests.py
```

I spent about eight hours creating this.

Possible improvements
---------------------

* Support more log formats than just this one CSV schema
* Send alerts to a pager service
* Include outlier characteristics in alerts (for example, "host 10.0.0.1 accounts for 90% of the traffic in this window")
* Calculate performance against an SLO based on availability tracking
* Support multiple alert types (maybe even configurable) beyond avg event count per time window
* Keep sliding window sorted to enable more efficient window pruning
