FROM quay.io/keycloak/keycloak:21.1.1

ENV JAVA_OPTS="-Dmail.smtp.ssl.trust=smtp.gmail.com"

EXPOSE 8080 587

CMD ["-v", "start-dev", "--import-realm"]