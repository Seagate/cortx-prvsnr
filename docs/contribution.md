# Contribution Guide

Contribution is always welcomed and appreciated!

How can I contribute:
  - raise an issue or a feature request
  - fix an issue or implement a feature
  - improve documentation
  - improve testing coverage

And the last but the most improtant thing is to raise a merge
request with any changes listed above.


## Issue reports and feature requests

Options:
- [issue tracker](http://gitlab.mero.colo.seagate.com/ivan.alekhin/public/issues)
- [JIRA](https://jts.seagate.com/)


## Improve Documentation

TODO

## Write Tests

TODO

## Merge Requests

Each merge request should pass a list of checks before it can be merged:
- code review
- automatic verification

### Code Review

The goal of the code review process is to ensure that a request:
- follows some good practicies of the project
- doesn't break any existing logics
- addresses the actual topic of the requests
- does that in an optimal way
- and covers all that with a good set of automated tests

Who reviews:
- Code review helps any developer to be aware of the project codebase and coming changes.
  So, review might be done by any developer and anyone is encouraged to do that
  and comment on any found issues or uncertain places.

How to ask for a review:
- please mark the request as WIP if it's not ready for the review
- unmark WIP and mention in the comment OR assign the request to a reviewer(s)
  when the request is ready
- if code review has not happened for a more than few days please feel free
  to re-reassign or mention other reviewr(s)


### Automatic Verification

The goals of the verification is to help with code quality validation.

It includes:
- static checks:
    - python linting
    - yaml linting
- dynamic checks:
    - unit testing
    - integration testing

A rule of thunb for any contributor is to verify that all these checks
are passed locally before pushing changes to the remote.
