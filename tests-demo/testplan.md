This is my test plan! It's pretty simple, and I'm curious to see where the discussion goes when we meet.

1. the portion of the feature under test
    upgrade functionality
2. the type of test to be run
    Integration and unit tests
3. test inputs and expected outputs for passing and not passing cases
    listing page
        not enabled
            Cypress: the page shows a list of farms, clicking does nothing
        enabled
            assuming some farms in the test account:
                cypress: the page shows a list of farms, clicking opens a new pane
                cypress: new pane shows three graphs, summary number is visible
                python: the functions generating the graphs generate proper output given expected input
            assuming no farms in the test account:
                cypress: the page shows an empty list of farms, clicking does nothing
    upgrade page
        not enabled
            cypress: upgrade button is visible, clicking it causes upgrade
        enabled
            cypress: page redirects to documentation
4. the tools used to run the test
    Cypress, Python
