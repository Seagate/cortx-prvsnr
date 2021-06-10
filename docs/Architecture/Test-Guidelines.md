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

A group of test cases can be run together by placing them under a common “marker” name or by a common string in the method name as `test_deploy` or file name as `test_deploy.py`.

```
python3 -m pytest -m <marker> -s
```

OR

```
python3 -m pytest -k <string> -s
```

A better approach would be to follow the use of string in file name, as we have better control in grouping all related-test cases together.

## Proposed Directory Design

* The proposed design will not deviate a lot from the existing architecture, instead will only aim to streamline some scattered tests. This design will be updated/changed based on further discussions and design requirements.

* The idea is to create a "Suite"-like design which will group all the related test cases and execute.


### Integration Tests

**Design Features**
* A Test Case (TC) must be the smallest functional element and should not combine multiple logic together. For instance, test cases implemented specific to bootstrap functionality must not include other functionalities.

* All individual TestCases must follow the below naming convention:
  * Start with “test_ “, followed by corresponding test suite name, followed by the function they represent, followed by test case definition.
  * Ex: `test_deploy_bootstrap_ssh`, `test_deploy_bootstrap_configure`, etc.

    **Format:**
    ```
    test_<testsuite>_<function>_<definition>
    ```

* A Test Suite (TS) can be broken down to multiple other test suites based on the functions it represents and need not contain “test_ “ in its name.

* A Test Module (TM) is an even larger collection of test suites and will form the root parent folder structure and need not contain “test_ “ in its name.

* Test Suite and Test Module are always directories and Test Case is a python file with one or more methods implemented.

* Each Test Suite (sub-directories) may contain a config file `pytest.ini` which would ideally contain the file names inside that directory.
  * This is an option to make testing easier. As we add or remove more files in future to a particular directory, the file names can be listed here and only those would be executed.
  * Removing any file name from `pytest.ini` will not have an overall effect in execution of that Test Module. This is only for testing the methods in given Test Suite.

  * Example, say a Test Suite (sub-directory named `pre_deploy`) has 5 files, and only 2 have to be tested new, then it can included as,

    ```
    [pytest]
    python_files = test_network_checks.py test_env_setup.py

    ```
    **Execution:**

    ```
    [root@xxx pre_deploy]# ls
    __pycache__  pytest.ini  test_driver_setup.py  test_env_setup.py  test_network_checks.py  test_storage_checks.py  test_ssh.py

    [root@xxx pre_deploy]# pytest
    ========================================================== test session starts ==========================================================
    platform linux -- Python 3.6.8, pytest-5.1.1, py-1.10.0, pluggy-0.13.1
    rootdir: /root/test/deploy/pre_deploy, inifile: pytest.ini
    plugins: mock-3.4.0, forked-1.3.0, testinfra-3.1.0, xdist-1.29.0, shell-0.2.3, timeout-1.3.4
    collected 4 items

    test_env_setup.py ..                                                                                                                  [ 50%]
    test_network_checks.py ..                                                                                                             [100%]

    =========================================================== 4 passed in 0.08s ===========================================================
    [root@xxx pre_deploy]# 

    ```

* Additionally, PyTest also provides another default config file - `conftest.py`, which is used to import test fixture function to be used in multiple test files and to import external plugins or modules.
  * It is ideally present in the test/ root folder and can be used to ignore any files from being considered for testing.
  * This would be useful in case of exclusion of framework-specific files like `setup.py` which is not necessary to include in PyTest execution.

* *NOTE:* All the test names are sample and design ideas are liable to more changes.


**Test Hierarchy and Design**

For Integration tests, here are the formats of Test Framework Hierarchy and Design.

![test_folder_hierarchy_v2](https://user-images.githubusercontent.com/70517184/103939459-ce48a400-5151-11eb-943f-6288cd248b53.png)


**A more scrutinized format of this hierarchy:**

![test_guidelines_design_v2](https://user-images.githubusercontent.com/70517184/103944818-3c916480-515a-11eb-8893-52c1a284e622.png)



**Sample Folder Structure**

The existing `test/` folder can look similar to this format.

```
test
├── api/python
│   └── deploy
│   │   └── deploy_setup
│   │      ├── bootstrap
│   │      │   └── test_deploy_bootstrap_ssh.py
│   │      │   ├── pytest.ini
│   │      │   └── deploy_unittest
│   │      └── setup_prvsnr
│   │          └── setup_env
│   │          ├── pytest.ini
│   │          └── setup_prvsnr_unittest
│   └── sw_update
│   │   └── sw_update_setup
│   │       ├── sw_update_repo
│   │       │   └── test_configure_repo.py
│   │       ├── pytest.ini
│   │       └── sw_update_unittest
│   └── repl_node
│       └── repl_node_setup
│           ├── m5_user_profile
│           │   └── test_m5_verify_alias.py
│           ├── pytest.ini
│           └── repl_node_unittest
├── cli/src
│    └── factory_pkg
│       └── boxing
│       │   ├── test_boxing_ctrl_ip_validate.py
│       │   ├── pytest.ini
│       │   └── boxing_unittest
│       └── unboxing
│           ├── test_unboxing_status.py
│           ├── pytest.ini
│           └── unboxing_unittest
├── srv/components
│   └── configuration
│       └── setup_minion
│           ├── test_salt_validate_minions.py
│           ├── pytest.ini
│           └── setup_minion_unittest
└── conftest.py

```

With the above design structure, execution of deploy-related test cases can be either one of the following ways,

```
python3 -m pytest -m deploy -s
```

OR

```
pytest deploy/
```
For specific execution of deploy-bootstrap-related test cases,

```
python3 -m pytest -m bootstrap -s
```

OR

```
pytest deploy/bootstrap/
```

OR

```
cd deploy/bootstrap
pytest
```

### Unit Tests

Unit testing is a way to test a single unit of software. For example, testing a utility function that changes the Array/List of characters to a string. Unit testing is the best way to be sure that your functions work as expected.

The goals of the kind of testing outlined here are simplicity, loose or no coupling, and speed:

Tests should be as simple as possible, while exercising the application-under-test (AUT) completely.
Tests should run as quickly as possible, to encourage running them frequently.
Tests should avoid coupling with other tests, or with parts of the AUT which they are not responsible for testing.

-Following are some links to start writing unit tests by following guidelines:

  -[https://pylonsproject.org/community-unit-testing-guidelines.html]

  -[https://realpython.com/python-mock-library/]

  -[https://docs.python-guide.org/writing/tests/]

  -[https://docs.python.org/3/library/unittest.mock-examples.html]
