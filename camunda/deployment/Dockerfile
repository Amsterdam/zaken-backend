FROM openjdk:13.0.2

ADD adp_rootca.crt /
ADD nl_root.crt /
ADD *.jar /app.jar

RUN keytool -trustcacerts -keystore "/usr/java/openjdk-13/lib/security/cacerts" -storepass changeit -importcert -alias nl_root_crt -file "/nl_root.crt" -noprompt
RUN keytool -trustcacerts -keystore "/usr/java/openjdk-13/lib/security/cacerts" -storepass changeit -importcert -alias xxx_crt -file "/adp_rootca.crt" -noprompt

#you need the crazy-looking filename, e.g., the extra /./, to trick Java into accepting your filename. If you just use /dev/urandom, Java decides you didn't really mean it and replaces what you wrote with /dev/random. Craziness!
ENTRYPOINT ["java","-agentlib:jdwp=transport=dt_socket,server=y,address=*:8000,suspend=n","-Xms1024M","-Xmx1024M","-Djavax.net.ssl.trustStore=/usr/java/openjdk-13/lib/security/cacerts","-Djavax.net.ssl.trustStorePassword=changeit","-Djava.security.egd=file:/dev/./urandom","-jar","/app.jar"]



# FROM camunda/camunda-bpm-platform:latest

# # ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt
