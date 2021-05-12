FROM openzaak/open-notificaties

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

# Setup Certificates for ADP/Motiv
ADD certificates/adp_rootca.crt /usr/local/share/ca-certificates/adp_rootca.crt
RUN chmod 644 /usr/local/share/ca-certificates/adp_rootca.crt \
    && update-ca-certificates --fresh

# TODO: this is a mock cmis_mapper, based on https://github.com/open-zaak/open-zaak/blob/master/config/cmis_mapper.json
# Update this once we have received the definite mapping
ADD cmis/cmis_mapper.json /app/cmis/cmis_mapper.json
