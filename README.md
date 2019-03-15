<h1 align="center">
  <br>
        <a href="https://decodeproject.eu/">
                <img src="https://decodeproject.eu/sites/all/themes/marmelo_base/img/logo.svg" width="300" alt="dddc-petition-api">
        </a>
  <br>
  DDDC Petition API
  <br>
</h1>


| Restful API for the PETITIONS of the Digital Democracy and Data Commons pilot project |
:---:
| [![Build Status](https://travis-ci.com/DECODEproject/dddc-petition-api.svg?branch=master)](https://travis-ci.com/DECODEproject/dddc-petition-api) [![codecov](https://codecov.io/gh/DECODEproject/dddc-petition-api/branch/master/graph/badge.svg)](https://codecov.io/gh/DECODEproject/dddc-petition-api) [![Dyne.org](https://img.shields.io/badge/%3C%2F%3E%20with%20%E2%9D%A4%20by-Dyne.org-blue.svg)](https://dyne.org) |

<br><br>

Petition API is part of the DDDC.

Digital Democracy and Data Commons is a pilot participatory process oriented to test a new technology to improve the 
digital democracy platform Decidim and to collectively imagine the data politics of the future.

This pilot takes place in the context of the European project 
[DECODE (Decentralized Citizen Owned Data Ecosystem)](https://decodeproject.eu) that aims to construct legal, 
technological, and socioeconomic tools that allow citizens to take back control over their data and 
[technological sovereignty](https://www.youtube.com/watch?v=RvBRbwBm_nQ).
 
Our effort is that of improving people's awareness of how their data is processed by algorithms, as well facilitate the
work of developers to create along
[privacy by design principles](https://decodeproject.eu/publications/privacy-design-strategies-decode-architecture) 
using algorithms that can be deployed in any situation without any change.


<details>
 <summary><strong>:triangular_flag_on_post: Table of Contents</strong> (click to expand)</summary>

* [Getting started](#rocket_getting-started)
* [Install](#floppy_disk-install)
* [Usage](#video_game-usage)
* [Docker](#whale-docker)
* [API](#honeybee-api)
* [Configuration](#wrench-configuration)
* [Testing](#clipboard-testing)
* [Troubleshooting & debugging](#bug-troubleshooting--debugging)
* [Acknowledgements](#heart_eyes-acknowledgements)
* [Links](#globe_with_meridians-links)
* [Contributing](#busts_in_silhouette-contributing)
* [License](#briefcase-license)
</details>

***
## :rocket: Getting started

> This requires docker to be installed


```bash
git clone --recursive https://github.com/DECODEproject/dddc-petition-api.git
cd dddc-petition-api
./start.sh
```

This will clone the project and all submodules of the project (**--recursive** is important)
then by lunching the `start.sh` will create a docker container with all the dependencies correctly
configured.

Head your browser to:

**SWAGGER UI**: http://0.0.0.0/docs/

**API**: http://0.0.0.0/ 

***
## :floppy_disk: Install

To locally run you need to run over a the API project over an [ASGI](https://asgi.readthedocs.io/en/latest/) server 
like [uvicorn](https://www.uvicorn.org/).

Assuming you are already cloned the project as described on [Getting started](#rocket_getting-started) with the 
submodules and already `cd` into your project directory `dddc-petition-api` you need the following steps

1. create a `virtualenv`
1. activate the virtualenv
1. upgrade the pip
1. install dependencies
1. install the ASGI server
1. run locally the API

```bash
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install uvicorn
uvicorn app.main:api --log-level debug --reload
```


***
## :video_game: Usage

This API server is meant for the Petition of the DDDC Project part of the DECODE project.

***
## :whale: Docker

```bash
docker build -t dddc-petition-api .
docker run --rm -p 80:80 -e APP_MODULE="app.main:api" -e LOG_LEVEL="debug" -it dddc-petition-api
```

All the options are documented on [here](https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker#advanced-usage)

***
## :honeybee: API

All the parameters and format of the input are documented on the swagger, below you'll find a quick description of each
endpoint 


#### /
Hello world endpoint

***
## :wrench: Configuration

```bash
export DEBUG=true
export ROOT_SRC=${HOME}/src/dddc-petition-api

export DB_URL=sqlite:///${ROOT_SRC}/db.sqlite3

export JWT_ALGORITHM=HS256
export JWT_TOKEN_SUBJECT=access
export JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
export JWT_USERNAME=***
export JWT_PASSWORD=***
export JWT_RANDOM_SECRET=***

export CONTRACTS_DIR=${ROOT_SRC}/app/contracts/src/

export CREDENTIAL_ISSUER_USERNAME=***
export CREDENTIAL_ISSUER_PASSWORD=***
export CREDENTIAL_ISSUER_CREDENTIALS_DIR=${ROOT_SRC}/app/credentials/

export PETITION_CONTROL_TOKEN=***
```

### Credentials folder
The credential folder contains credential previously created from the credential issuer and are store in file per `sha256(credential_issuer_id)` and the following three things are stored:

 * the credential object (output of 06-CITIZEN-aggregate-credential-signature.zencode) in form of filename **HEX**
 * the verifier keys of the credential issuer (04-CREDENTIAL_ISSUER-publish-verifier.zencode) **HEX.verify**
 * the private petition-api keys (01-CITIZEN-credential-keygen.zencode) **HEX.keys**
 
 Eg. if the `CREDENTIAL_ISSUER_CREDENTIALS_DIR=${ROOT_SRC}/app/credentials/` and the `credential_issuer_uid='issuer_identifier'` like https://petitions.decodeproject.eu/uid then the folder /app/credentials contains the following files:
 
 ```
3b2332e905bd662448d7114d0626421b82deb33fcf3bafe3c284bdfb9f58e2c6
3b2332e905bd662448d7114d0626421b82deb33fcf3bafe3c284bdfb9f58e2c6.keys
3b2332e905bd662448d7114d0626421b82deb33fcf3bafe3c284bdfb9f58e2c6.verify
 ```


***
## :clipboard: Testing

```bash
python3 setup.py test
```

***
## :bug: Troubleshooting & debugging

To run the `petition-api` in debug mode, please run it in local and activate `--debug` when you launch the ASGI
uvicorn server. 

Set the `LOG_LEVEL="debug"` ENVIRONMENT VARIABLE that is used by `uvicorn` and `starlette`.


***
## :heart_eyes: Acknowledgements

Copyright :copyright: 2019 by [Dyne.org](https://www.dyne.org) foundation, Amsterdam

Designed, written and maintained by Puria Nafisi Azizi.

<img src="https://zenroom.dyne.org/img/ec_logo.png" class="pic" alt="Project funded by the European Commission">

This project is receiving funding from the European Union’s Horizon 2020 research and innovation programme under grant 
agreement nr. 732546 (DECODE).


***
## :globe_with_meridians: Links

https://decodeproject.eu/

https://dyne.org/

https://zenroom.dyne.org/

https://dddc.decodeproject.eu/


***
## :busts_in_silhouette: Contributing

Please first take a look at the [Dyne.org - Contributor License Agreement](CONTRIBUTING.md) then

1.  :twisted_rightwards_arrows: [FORK IT](https://github.com/puria/README/fork)
2.  Create your feature branch `git checkout -b feature/branch`
3.  Commit your changes `git commit -am 'Add some fooBar'`
4.  Push to the branch `git push origin feature/branch`
5.  Create a new Pull Request
6.  :pray: Thank you


***
## :briefcase: License

	DDDC Petition API
    Copyright (c) 2019 Dyne.org foundation, Amsterdam

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License as
	published by the Free Software Foundation, either version 3 of the
	License, or (at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.

	You should have received a copy of the GNU Affero General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.

