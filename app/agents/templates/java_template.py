from typing import Dict, Any, List
from .base_template import BaseTemplate

class JavaTemplate(BaseTemplate):
    def get_language_name(self) -> str:
        return "Java"
    
    def get_file_extensions(self) -> List[str]:
        return ['.java', '.gradle', '.xml']
    
    def get_dockerfile_template(self) -> str:
        return """FROM openjdk:17-jre-slim
WORKDIR /app
COPY target/{service_name}.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]"""
    
    def get_prerequisites(self) -> str:
        return "Java 17+ and Maven/Gradle"
    
    def get_local_run_instructions(self, service_name: str) -> str:
        service_name_lower = service_name.lower()
        return f"""```
# Build with Maven
mvn clean install

# Run the application
java -jar target/{service_name_lower}.jar
```"""
    
    def generate_main_files(self, service_name: str) -> List[Dict[str, str]]:
        service_name_lower = service_name.lower()
        return [
            {
                "path": f"{service_name}/src/main/java/com/{service_name_lower}/Application.java",
                "content": f"""package com.{service_name_lower};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {{
    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}
}}"""
            },
            {
                "path": f"{service_name}/src/main/java/com/{service_name_lower}/controller/HealthController.java",
                "content": f"""package com.{service_name_lower}.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;

@RestController
@RequestMapping("/api/health")
public class HealthController {{
    
    @GetMapping
    public Map<String, String> health() {{
        return Map.of("status", "healthy", "service", "{service_name}");
    }}
}}"""
            },
            {
                "path": f"{service_name}/pom.xml",
                "content": f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.{service_name_lower}</groupId>
    <artifactId>{service_name_lower}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
    </dependencies>
</project>"""
            },
            {
                "path": f"{service_name}/src/main/resources/application.yml",
                "content": f"""server:
  port: 8080
spring:
  application:
    name: {service_name_lower}
logging:
  level:
    root: INFO
management:
  endpoints:
    web:
      exposure:
        include: health,info"""
            }
        ]
