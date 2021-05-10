FROM openjdk:13.0.2

ADD adp_rootca.crt /
ADD *.jar /app.jar

RUN keytool -trustcacerts -keystore "/usr/java/openjdk-13/lib/security/cacerts" -storepass changeit -importcert -alias adp_rootca -file "/adp_rootca.crt"

#you need the crazy-looking filename, e.g., the extra /./, to trick Java into accepting your filename. If you just use /dev/urandom, Java decides you didn't really mean it and replaces what you wrote with /dev/random. Craziness!
ENTRYPOINT ["java","-agentlib:jdwp=transport=dt_socket,server=y,address=*:8000,suspend=n","-Xms1024M","-Xmx1024M","-Djavax.net.ssl.trustStore=/usr/java/openjdk-13/lib/security/cacerts","-Djava.security.egd=file:/dev/./urandom","-jar","/app.jar"]
