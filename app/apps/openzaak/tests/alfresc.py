import requests

response = requests.get("https://alfresco-api1-acc.amsterdam.nl/", cert=('/home/jorik/Documents/alfresco/client-cert-zaken_alfresco-api1-acc_amsterdam_nl.crt'))
response = requests.get("https://alfresco-api1-acc.amsterdam.nl/", verify='/home/jorik/Documents/alfresco/client-cert-zaken_alfresco-api1-acc_amsterdam_nl.crt')

response = requests.get("https://alfresco-api1-acc.amsterdam.nl/", verify=False)
