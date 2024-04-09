# Project Title

Service Email for Smart Ticket Tool.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
docker docker-compose
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
1. docker-compose up
```

```
2. call api to 'http://localhost:5001/test/test'
```

## Folder Structure Conventions
============================

> Folder structure options and naming conventions for software projects

### A typical top-level directory layout

    .
    ├── app                             # app
    │   ├── models                      # model database sqlalchemy
    │   ├── test                        # maincode function
    │   │   ├── __init__.py
    │   │   ├── controller.py
    │   │   ├── model.py
    │   │   └── route.py
    │   ├── __init__.py
    │   ├── db_utility.py
    │   └── general_utility.py
    ├── test                            # basic test
    │   ├── __init__.py
    │   └── test_basic.py
    ├── uwsgi                           # uwsgi config
    │   └── uwsgi.ini
    ├── .gitignore                      # ignorefile to git
    ├── config.env                      # file config
    ├── config.py                       # file config
    ├── docker-compose.yml              # docker-compose file
    ├── Dockerfile
    ├── manage.py                       # manage service
    └── requirement.txt                 # requirement file
    └── README.md

> Use short lowercase names at least for the top-level files and folders except
> `README.md`

## Linter

We use Pylint [pylint](https://www.pylint.org/)


## Deployment

Add additional notes about how to deploy this on a live system
```
When push code to repository will hook automate to gitlab ci/cd.
```

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

Rattanachai Aussawasot

## License

This project is licensed under OpenLandscape Co., Ltd. - see the [OpenLandscape Co., Ltd.](https://www.ols.co.th/)


