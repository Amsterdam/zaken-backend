import json
import os
from pathlib import Path


def load_response(file_name):
    current_path = Path(__file__)
    return json.loads(
        open(
            os.path.abspath(
                os.path.join(current_path.parent.absolute(), "files", file_name)
            )
        ).read()
    )

create_case_failure = load_response("create_case_failure.json")
create_document_failure = load_response("create_document_failure.json")
connect_case_and_document_failure = load_response(
    "connect_case_and_document_failure.json"
)
