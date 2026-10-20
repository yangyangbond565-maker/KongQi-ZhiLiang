package com.aqp.server;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.aqp.server.mapper")
public class AqpServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(AqpServerApplication.class, args);
    }
}
