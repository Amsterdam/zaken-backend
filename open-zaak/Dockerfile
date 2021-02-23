FROM openzaak/open-zaak

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

# Setup Certificates for ADP/Motiv
ADD certificates/adp_rootca.crt /usr/local/share/ca-certificates/adp_rootca.crt
RUN chmod 644 /usr/local/share/ca-certificates/adp_rootca.crt \
    && update-ca-certificates --fresh

# TODO: The cmis_mapper.json structure is still empty. Update once we have the correct input.
ADD cmis/cmis_mapper.json /app/cmis/cmis_mapper.json
