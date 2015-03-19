p13n
====

Personalization API

Quickstart
----------

First, ensure that you have `virtualenv` installed.
Then, set your app's secret key as an environment variable. For example, example add the following to `.bashrc`.

``` bash
export P13N_SECRET='something-really-secret'
```

Then run the following commands to bootstrap your environment.

```
$ make env
```

Then you can start up your dev server with:

```
$ make server
```

Deployment
----------

In your production environment, make sure the `P13N_ENV` environment variable is set to `"prod"`.

Shell
-----

To open the interactive shell, run:

```
$ make shell
```

Running Tests
-------------

To run all tests, run:

```
$ make test
```
