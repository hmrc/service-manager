package com.github.sullis.dropwizard.helloworld;

import org.codehaus.jackson.map.SerializationConfig;

import com.yammer.dropwizard.json.Json;

public class CustomJson extends Json {
	public CustomJson() {
		mapper.configure(SerializationConfig.Feature.INDENT_OUTPUT, true);
		mapper.configure(SerializationConfig.Feature.WRITE_DATES_AS_TIMESTAMPS, false);
    }
}
