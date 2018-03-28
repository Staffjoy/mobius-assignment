![Logo](https://i.imgur.com/LAuMuLi.png)

# Mobius - Service for assigning workers to shifts according to constraints

[![Moonlight contractors](https://www.moonlightwork.com/shields/python.svg)](https://www.moonlightwork.com/for/python?referredByUserID=1&referralProgram=maintainer&referrerName=Staffjoy)

[Staffjoy is shutting down](https://blog.staffjoy.com/staffjoy-is-shutting-down-39f7b5d66ef6#.ldsdqb1kp), so we are open-sourcing our code. Mobius is an applied mathematics microservice for assigning workers to shifts, subject to constraints like availability and worker availability. This tool relies on the [Gurobi](http://www.gurobi.com/) Python library, which is closed source. 

This tool was used for [Staffjoy V1 (Suite)](http://github.com/staffjoy/suite) customers, and Mobius (in conjunction with [Chomp](http://github.com/staffjoy/chomp)) replaced the previous [Autoscheduler](http://github.com/staffjoy/autoscheduler) algorithm.

## Credit

This repository was conceived and authored in its entirety by [@philipithomas](https://github.com/philipithomas). This is a fork of the internal repository. For security purposes, the Git history has been squashed and client names have been scrubbed from tests.

## Self-Hosting

If you are self-hosting Mobius, please make sure that you are using version `>=0.24` of the `staffoy` client (in `requirements.txt`). Then, modify `mobius/tasking.py` to include your custom domain - when initializing `Client()`, pass in your custom URL base, e.g. `Client(url_base="https://staffjoy.example.com/api/v2/, key=config.STAFFJOY_API_KEY, env=config.ENV)`,

 
# Project Mobius

Microservice for assigning workers to shifts subect to constraints and happiness.

## Running

Provision the machine with vagrant. When you first run the program or when you change `requirements.txt`, run `make requirements` to install and freeze the required libraries. 

```
vagrant up
vagrant ssh
# (In VM)
cd /vagrant/
make dependencies
```


## Formatting

This library uses the [Google YAPF](https://github.com/google/yapf) library to enforce PEP-8. Using it is easy - run `make fmt` to format your code inline correctly. Failure to do this will result in your build failing. You have been warned.


To disable YAPf around code that you do not want changed, wrap it like this:

```
# yapf: disable
FOO = {
    # ... some very large, complex data literal.
}

BAR = [
    # ... another large data literal.
]
# yapf: enable
```
