package com.github.sullis.dropwizard.helloworld;

import org.codehaus.jackson.map.Module;

import com.github.sullis.dropwizard.helloworld.resources.HelloWorldResource;
import com.yammer.dropwizard.Service;
import com.yammer.dropwizard.config.Environment;
import com.yammer.dropwizard.json.Json;

public class HelloWorldService extends Service<HelloWorldServiceConfiguration> {

    public static void main(String[] args) throws Exception {
        new HelloWorldService().run(args);
    }

	private HelloWorldService() {
		super("helloworld");
	}

	@Override
	protected void initialize(HelloWorldServiceConfiguration configuration,
			Environment environment) throws Exception {

		environment.addResource(HelloWorldResource.class);

	}

	@Override
	public Json getJson() {
		final CustomJson json = new CustomJson();
        for (Module module : getJacksonModules()) {
            json.registerModule(module);
        }
        return json;
	}

}
