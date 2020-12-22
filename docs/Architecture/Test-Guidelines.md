
# Test Guidelines

Table of Contents:

- [Test Guidelines](#test-guidelines)
  - [Overview](#overview)
  - [PyTest Framework](#pytest-framework)
  - [Proposed Directory Design](#proposed-directory-design)
    - [Integration Tests](#integration-tests)
    - [Unit Tests](#unit-tests)

## Overview

Test Design implementation is written in PyTest tool in Provisioner. The scope of this design proposal is to serve as a guide to write future test cases under a disciplined structure. This design, however, is valid for Integration tests only and, the Unit testcases will go into a separate unit test folder created under each corresponding sub-directory.

## PyTest Framework

PyTest is full-featured Python testing tool currently implemented in Provisioner.  
It is installed along with other dependencies as part of `test-requirements.txt` file execution. The latest installed version is 5.1.x.  
Execute the test cases in the directory with the command,

```
python3 -m pytest <test_case>
```

In the current directory and its subdirectories, PyTest will run all test files as:

```
test_*.py
```
**Execute Multiple test cases as a Group:**

A group of test cases can be run together by placing them under a common “marker” name or by a common string in the method name as `test_function`.

```
python3 -m pytest -m <marker> -s
```

OR

```
python3 -m pytest -k <string> -s
```

Example,
**FOR MARKER:**

Create the test case with the marker `patch_logging` while writing the method and execute all testcases created with the same marker name as,

```
@pytest.mark.patch_logging()

python3 -m pytest -m patch_logging -s
```

**FOR STRING IN FUNCTION NAME:**

```
def test_deploy_status()

python3 -m pytest -k deploy -s
```

## Proposed Directory Design

* The proposed design will not deviate a lot from the existing architecture, instead will only aim to streamline some scattered tests. This design will be updated/changed based on further discussions and design requirements.

* The idea is to create a "Suite" sort of design which will group all the related test cases and execute.


### Integration Tests

**Design Features**

* A Test Case (TC) must be the smallest functional element and should not combine multiple logic together. For instance, test cases implemented specific to bootstrap functionality must not include other functionalities.

* All individual TestCases must follow the below naming convention:
  * Start with “test_ “, followed by corresponding test suite name, followed by the function they represent, followed by test case definition.
  * Ex: `test_deploy_bootstrap_ssh`, `test_deploy_bootstrap_configure`, etc.

```
Format:

test_<testsuite>_<function>_<definition>
```

* A Test Suite (TS) can be broken down to multiple other test suites based on the functions it represents.

* A Test Module (TM) is an even larger collection of test suites and will form the root parent folder structure.

* Test Suite and Test Module are always directories and Test Case is a file with one or more methods implemented.


**Test Hierarchy and Design**

For Integration tests, here are the formats of Test Framework Hierarchy and Design.

![test_folder_hierarchy](https://user-images.githubusercontent.com/70517184/102914245-fa073100-44a5-11eb-8a7d-5da0efa7b538.png)

A more scrutinized format of this hierechy: 

![test_guidelines_design](https://user-images.githubusercontent.com/70517184/102914340-21f69480-44a6-11eb-8b28-d90752596ae9.png)

**Sample Folder Structure** 

The existing `test/` folder can look similar to this format.

```
test
├── test_api
│   └── python
│       ├── files
│       │   └── conf_file
│       ├── test_deploy
│       │   ├── test_bootstrap
│       │   │   └── test_deploy_bootstrap_ssh.py
│       │   └── test_deploy_unittest
│       ├── test_repl_node
│       │   ├── test_cluster
│       │   │   └── test_repl_node_cluster_status.py
│       │   └── test_repl_node_unittest
│       └── test_sw_update
│           ├── test_sw_update_repo
│           │   └── test_sw_update_repo_configure.py
│           └── test_sw_update_unittest
├── test_cli
│   └── src
│       └── test_boxing
│           └── test_boxing_bmc
│               └── test_boxing_bmc_accessible.py
├── test_srv
│   └── components
│       └── test_salt
│           ├── test_salt_validate_minions.py
│           ├── test_sw_update_unittest
└── conftest.py

```

### Unit Tests 

This proposed design is more suited for Integration Tests, so the Unit Tests can either be placed under a separate `unittest` folder created for each group as explained in the above Design diagram or can be placed under the existing mirrored architecture in `test/` folder.  

