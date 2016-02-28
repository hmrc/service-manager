#! /bin/sh
# This is kind of cheating i should put in services.json, but im just trying to get this working at the moment
mvn clean package
java -jar target/dropwizard-helloworld-0.0.1-SNAPSHOT.jar server config/dev_config.yml