import re

from bs4 import BeautifulSoup


def get_forms(html):
    """Returns all form tags found on a web page's `url` """
    soup = BeautifulSoup(html, "html.parser")
    return soup.find_all("form")


def get_form_details(form):
    """
    Return a dictionary of the html form, including input types and
    """
    details = {}
    # get all form inputs
    inputs = []
    for input_tag in form.find_all("input"):
        # get type of input form control
        input_type = input_tag.attrs.get("type", "text")

        # get the Camunda type
        camunda_input_type = input_tag.attrs.get("cam-variable-type")

        # get name attribute
        input_name = input_tag.attrs.get("name")

        # get the default value of that input tag
        input_value = input_tag.attrs.get("value", "")

        # Get the label for the input field
        # TODO: Validate that this works on radiobuttons. Depending on how the radiobuttons are rendered, we might have to rewrite this.
        label = form.find("label", attrs={"for": input_name}).contents[0].strip()

        # Required field.
        required = (
            input_tag.parent.find(string=re.compile("Required field")) is not None
        )

        # Check for a date field
        is_date = input_tag.parent.find(string=re.compile(".date")) is not None

        # add everything to that list
        inputs.append(
            {
                "type": input_type,
                "camunda_type": camunda_input_type,
                "name": input_name,
                "default_value": input_value,
                "label": label,
                "required": required,
                "is_date": is_date,
            }
        )

    details["inputs"] = inputs
    return details
