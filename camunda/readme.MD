Stap 1:
```gradlew buildDockerImage```

Stap 2:
```docker run -e API_KEY=test1234 -e LOGGING_LEVEL=DEBUG -p 8080:8080 gemeente-amsterdam-wonen-camunda:0.0.1```
