Service Manager
===================

Developing with lots of microservices often draws complaints from the eventual complexity for the developer. i.e. 10 different services to start that are constantly evolving, owned by different teams and using different technologies... What if there was a way to manage this so you can just get on with your work...

Introducing Service Manager

A set of utilities to run applications and micro services during the development and testing phase... and make development easier in a micro service environment

####[How do I install?](https://github.com/hmrc/service-manager/wiki/Install#install-service-manager)

####[How do I setup?](https://github.com/hmrc/service-manager/wiki/Required-Environment-Settings)

#Common use cases / Getting started
For a list of commands type 'sm --help'
For current run status type 'sm -s'

Starting all services using binaries:
sm --start "*" -f

#Adding a new application
###1. Modify your services.json file 
The application automatically looks for your config in `$WORKSPACE/service-manager-config`

You can change this directly in $WORKSPACE/service-manager-config to test your changes locally

Add a new application at the bottom of the services.json. 
There are plenty of example of how to do this by looking at existing entries

#SM Server
Service Manager also has a feature for allowing integration tests

run smserver and it will run a service that can fire up services on demmand

## API

| Path                                   | Supported Methods | Description  |
| -------------------------------------- | ------------------| ------------ |
|```/ping```             |        GET        ||
|```/start```             |        POST        ||
|```/stop```             |        POST        ||
|```/version_variable```             |        GET        ||
