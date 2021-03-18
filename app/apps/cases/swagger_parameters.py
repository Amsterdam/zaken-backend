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

start_date = OpenApiParameter(
    name="startDate",
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Start Date",
)

open_cases = OpenApiParameter(
    name="openCases",
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Open Cases",
)

team = OpenApiParameter(
    name="team",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Team to which the cases should belong",
)

reason = OpenApiParameter(
    name="reason",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Case Reason",
)

open_status = OpenApiParameter(
    name="openStatus",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Case Status",
)
