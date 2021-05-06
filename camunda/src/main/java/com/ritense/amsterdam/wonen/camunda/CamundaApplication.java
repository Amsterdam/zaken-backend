package com.ritense.amsterdam.wonen.camunda;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration;

@SpringBootApplication(exclude = { SecurityAutoConfiguration.class })
public class CamundaApplication {

	public static void main(String[] args) {
		SpringApplication.run(CamundaApplication.class, args);
	}

}
