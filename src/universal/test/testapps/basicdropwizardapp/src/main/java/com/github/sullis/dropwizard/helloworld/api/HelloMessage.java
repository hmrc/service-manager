package com.github.sullis.dropwizard.helloworld.api;

import java.util.Date;

public class HelloMessage {
	private String message = "Hello";
	private Date timestamp = new Date();

	public Date getTimestamp() {
		return timestamp;
	}
	public void setTimestamp(Date timestamp) {
		this.timestamp = timestamp;
	}

	public String getMessage() {
		return message;
	}

	public void setMessage(String msg) {
		message = msg;
	}

}
