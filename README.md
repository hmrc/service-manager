Service Manager
===================

Developing with lots of microservices often draws complaints from the eventual complexity for the developer. i.e. 10 different services to start that are constantly evolving, owned by different teams and using different technologies... What if there was a way to manage this so you can just get on with your work...

Introducing Service Manager

A set of utilities to run applications and micro services during the development and testing phase... and make development easier in a micros service environment

#Prerequsites

### Pip
Install pip

https://pypi.python.org/pypi/pip

### Install required python packages with pip

run:

pip install -qr requirements.txt

### Nexus Credentials

Nexus credentials can come from one of multiple sources:

1) Environment variables
```
export NEXUS_PASS=<nexus-password>
export NEXUS_USER=<nexus-username>
```
the NEXUS_PASS and NEXUS_USER environment variable names can be customised to your needs in config.json e.g.
```
{
 "nexusPasswordEnvironmentVar":"MY_NEXUS_PASS_ENV_VAR",
 "nexusUserEnvironmentVar":"MY_NEXUS_USER_ENV_VAR"
}
```
2) Credentials file
```
user=<nexus-username>
password=<nexus-password>
```
This information should live in ~/.sbt/.credentials, but the location can also be customised in config.json e.g.
```
{
 "sbtCredentialsFile":"/path/to/my/credentials/file"
}
```

### Scripts project

Clone the [Scripts project](https://github.tools.tax.service.gov.uk/HMRC/scripts)
`git clone git@github.tools.tax.service.gov.uk:HMRC/scripts.git`

# Required environmental variables

Please ensure these enviroment variables have been exported.

```
WORKSPACE=<root-path>/hmrc-development-environment/hmrc/
JAVA_HOME=location_of_your_java (can be found by typing which java)
jenkins_user="<nexus-username>"
jenkins_key="<jenkins-api-token>"
```
You can get your Jenkins API Token by:

1. Visit [CI-DEV](https://ci-dev.tax.service.gov.uk/)
2. Click your username top right to visit your profile
3. Select configure on the left
4. Press 'Show API Token...'
5. Copy and paste that token into the `jenkins_key` export.

### Getting service-manager-config

Before you are able to run the Application Manager you need to get the config.
You will need to be connected to the VPN to do this.

You can do this by:

```
cd $WORKSPACE/scripts && \
./get-service-manager-config.sh
```

#Common use cases / Getting started
For a list of commands type './sm.py --help'
For current run status type './sm.py -s'

Starting all services using binaries:
./sm.py --start "*" -f

#Adding a new application
###1. Modify your services.json file 
The application automatically looks for your config in `$WORKSPACE/service-manager-config`

You can change this directly in $WORKSPACE/service-manager-config to test your changes locally, 
however, to make these changes permanently, you will need to modify the file in puppet:

(for hmrc this is in the [puppet repo] )
[puppet repo]: https://github.tools.tax.service.gov.uk/HMRC/puppet/tree/master/modules/hmrc_smserver/files  "here"

Add a new application at the bottom of the services.json. 
There are plenty of example of how to do this by looking at existing entries

###2. Create a pull request in puppet with the above changes!!

#Getting / Updating configuration

A script exists here:
https://github.tools.tax.service.gov.uk/HMRC/scripts/blob/master/get-service-manager-config.sh

run this to get the latest changes to the service manager configuration files from jenkins.

#Deploying smserver

Do it yourself via Jenkins! We have a job: service-manager-deploy
