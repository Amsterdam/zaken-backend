# Open Zaak Services
This module contains code for connecting with Open Zaak. It contains some abstractions such as a "Service" which allows to instantiate a service object for connecting to a specific domain and data type within Open Zaak (or other APIs), for example a Catalog or a State Type. An example of how this could be used for Catalogs can be found in example/catalog/

The code in connection.py is perhaps the most useful. It's basic code to handle authentication and requests with an Open Zaak instance.

This modules serves mostly as documentation of an earlier approach in this project, in which this application was just a simple 'gateway' or layer on top of Open Zaak. The approach didn't meet our needs, but some of the results are distilled in this module, to be used at a later point in time.
