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

date = OpenApiParameter(
    name="date",
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Shows cases that started on the given date",
)

start_date = OpenApiParameter(
    name="startDate",
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Shows cases that started from that date and later",
)

open_cases = OpenApiParameter(
    name="openCases",
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Open Cases",
)

theme = OpenApiParameter(
    name="theme",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Theme to which the cases should belong",
)

reason = OpenApiParameter(
    name="reason",
    type=OpenApiTypes.INT,
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

no_pagination = OpenApiParameter(
    name="noPagination",
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Disable Pagination",
)

ton_ids = OpenApiParameter(
    name="tonIds",
    type=OpenApiTypes.STR,  # drf_spectacular doesn't support arrays, not so spectacular after all...
    location=OpenApiParameter.QUERY,
    required=False,
    description="One or more TON IDs, comma separated",
)
