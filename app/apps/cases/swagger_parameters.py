from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

postal_code = OpenApiParameter(
    name="postalCode",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Postal Code",
)

street_number = OpenApiParameter(
    name="streetNumber",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Street Number",
)

street_name = OpenApiParameter(
    name="streetName",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Street Name",
)

suffix = OpenApiParameter(
    name="suffix",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Suffix",
)

team = OpenApiParameter(
    name="team",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Team to which the cases should belong",
)

case_search_parameters = [postal_code, street_number, street_name, suffix, team]
