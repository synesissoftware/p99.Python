# p99.Python <!-- omit in toc -->

Low-cost performance percentiles (p50, p90, p99, …), for Python

![Language](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![PyPI](https://img.shields.io/pypi/v/p99.svg)](https://pypi.org/project/p99/)
[![GitHub release](https://img.shields.io/github/v/release/synesissoftware/p99.Python.svg)](https://github.com/synesissoftware/p99.Python/releases/latest)
[![Last Commit](https://img.shields.io/github/last-commit/synesissoftware/p99.Python)](https://github.com/synesissoftware/p99.Python/commits/master)
[![CI](https://github.com/synesissoftware/p99.Python/actions/workflows/python-package.yml/badge.svg)](https://github.com/synesissoftware/p99.Python/actions/workflows/python-package.yml)
![Python](https://img.shields.io/badge/Python-2.7%20%7C%203.8+-lightgrey)


## Table of Contents <!-- omit in toc -->

- [Introduction](#introduction)
- [Installation](#installation)
- [Components](#components)
- [Project Information](#project-information)
  - [Where to get help](#where-to-get-help)
  - [Contribution guidelines](#contribution-guidelines)
  - [Dependencies](#dependencies)
    - [Efferent (fan-out)](#efferent-fan-out)
    - [Development Dependencies](#development-dependencies)
    - [Afferent (fan-in)](#afferent-fan-in)
  - [Related projects](#related-projects)
  - [License](#license)


## Introduction

**p99** provides very low-cost measuring of performance percentiles (p50, p90, p99, and so on).

**p99.Python** is the **Python** implementation. It supports **Python 2.7** and **Python 3.8+**. This repository is a packaging skeleton; the percentile API is not implemented yet.


## Installation

Install via **pip**:

```
pip install p99
```

Use via **import**:

```Python
import p99

print(p99.__version__)
```


## Components

Skeleton; API not yet implemented.


## Project Information


### Where to get help

[GitHub Page](https://github.com/synesissoftware/p99.Python "GitHub Page")


### Contribution guidelines

Defect reports, feature requests, and pull requests are welcome on https://github.com/synesissoftware/p99.Python.


### Dependencies


#### Efferent (fan-out)

None.


#### Development Dependencies

* [**pytest**](https://docs.pytest.org/);
* [**ruff**](https://docs.astral.sh/ruff/);


#### Afferent (fan-in)

None (currently).


### Related projects

* [**p99** (C)](https://github.com/synesissoftware/p99);
* [**p99.Go**](https://github.com/synesissoftware/p99.Go);
* [**p99.NET**](https://github.com/synesissoftware/p99.NET);
* [**p99.Ruby**](https://github.com/synesissoftware/p99.Ruby);
* [**p99.Rust**](https://github.com/synesissoftware/p99.Rust);
* [**p99.Zig**](https://github.com/synesissoftware/p99.Zig);


### License

**p99.Python** is released under the 3-clause BSD license. See [LICENSE](./LICENSE) for details.


<!-- ########################### end of file ########################### -->
