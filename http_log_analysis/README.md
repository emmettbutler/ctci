HTTP Logfile Analyzer
=====================

This is a tool that facilitates simple analysis on HTTP logfiles formatted as CSV. It also simulates real-time playback of the request log with a configurable timeout.

Run it with this command:

```sh
$ python main.py readme_sample_csv.txt --timescale 0.01
```

You can provide a different input file if you want. If you do, make sure it conforms to the same CSV schema as the txt file included here.

The "timescale" option controls the speed at which the log is played back. Without specifying this option, the log plays back as fast as your
machine can muster. When it's specified, `sleep` calls are added between log lines being consumed by the program, of length proportional to the
differences between arrival times in consecutive log lines. This is simply a fun way to explore this program's output as if you were tailing
a live logfile.

You can also adjust various analysis values at the CLI, including alert threshold and window size. Use this command for more details:

```sh
$ python main.py --help
```

This tool has no Python dependencies - it uses only the Python standard library. It's compatible with Python versions 3.7 and above.

You can run the unit test suite with this command:

```sh
$ python tests.py
```

Scaling
-------

This program could scale to large data volumes by reading multiple files in parallel using multiple processes. In that setup, each process would still maintain its
own independent monitors over only the files it's responsible for. Once this program was tuned to use all of the available resources on a single machine, it
could be deployed to multiple machines, reading multiple files on each.

Architecture
------------

This program is implemented as a chain of generators, where each generator performs a distinct functional requirement. The "chain" is created by having each generator return its input unchanged.
This generator chain is consumed with the rough equivalent of `for _ in gen: pass` to trigger program execution. A benefit of this design is that it ensures a minimum of data remains in memory at once,
and thus would scale relatively easily to larger volumes of data.

`read_access_log` returns a generator of objects representing individual validated log lines read from the disk. It also simulates live "playback" by optionally inserting `sleep`s.

`aggregate_stats` accepts that generator and returns the same sequence of objects. As it iterates, it builds time-based "buckets" of events and performs aggregate analysis on
each bucket in turn. These aggregates are managed by the `AccessLogAggregate` class.

`AccessLogMonitor.run` accepts a generator with the same contents and maintains a sliding window of recent event data. Every time it processes an event, it checks its alerting conditions
and triggers an alert if necessary.

Possible improvements
---------------------

* Support more log formats than just this one CSV schema
* Send alerts to a pager service
* Include outlier characteristics in alerts (for example, "status 500 from host 10.0.0.1 accounts for 90% of the traffic in this window")
* Calculate performance against an SLO based on availability tracking
* Support multiple alert types (maybe even configurable) beyond avg event count per time window
* Keep sliding window sorted to enable more efficient window pruning
* Consider organizing toplevel functions into a class interface

Notes
-----

I spent about eight hours creating this.

The Python code was linted with Black and Isort using [this vim config](https://github.com/emmettbutler/emmettbutler/blob/master/ansible/roles/development/files/nvim/init.lua).

The lack of requirements files is an intentional choice to make this program very easy to run. If there were third-party dependencies, they would
be managed using Poetry.
