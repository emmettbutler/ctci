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

This tool has no Python dependencies - it uses only the standard library.

You can run the unit test suite with this command:

```sh
$ python3.10 tests.py
```
