London weather forecasts in CSV format
--------------------------------------

Running locally
---------------

On a system with `make` and Docker installed, run `make` to create and run a container that runs this app.

`make build && make start`

If you don't have access to `make`, you can run the same Docker commands that the `Makefile` uses.

These commands will give you a shell in the app container, and a CSV of today's 5-day weather forecast for London will
be in your current working directory. Once you're done exploring, `exit` this shell, then use `make stop` to terminate
the container.

Running tests
-------------

You can run this project's unit tests with `make tests` or by running the commands from that section of the Makefile
directly.

Notes
-----

The "referenced later" JSON file from step 1 is `fixture.json`.
