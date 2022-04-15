Raptor Maps Test Demo
=====================

Important files:
* `cypress/integration/sample-spec.js`: core Cypress test logic for steps 1-5
* `testplan.md`: notes for test plan presentation
* `test_endpoint.py`: python-based tests of API endpoint

Running tests
-------------

Cypress:
```
$ npm install
$ ./node_modules/cypress/bin/cypress run
```

Python:
```
$ pip install -r requirements.txt
$ pytest
```
