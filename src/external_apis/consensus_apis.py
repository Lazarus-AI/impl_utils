import json
import os
from typing import Any

import requests


def send_smarty_request(
    address: str = None, city: str = None, state: str = None, zip: str = None
) -> Any:
    """
    Ping the Smarty API to validate address information.

    :param address: The street address.
    :param city: The city name.
    :param state: The state abbreviation.
    :param zip: The ZIP code.
    :return: The closest matching address to the information given in the input determined by the Smarty API, or None if inputs are insufficient.
    :raises Exception: If there are errors in the response or if the response is empty.
    """
    SMARTY_ENDPOINT = "https://us-street.api.smartystreets.com/street-address"
    params = {
        "auth-id": os.environ.get("SMARTY_AUTH_ID"),
        "auth-token": os.environ.get("SMARTY_AUTH_TOKEN"),
        "license": os.environ.get("SMARTY_LICENSE"),
    }

    if address and city and state:
        params.update({"street": address, "city": city, "state": state})
    elif address and zip:
        params.update({"street": address, "zipcode": zip})
    else:
        print("Not enough inputs available for Smarty")
        return None

    try:
        smarty_response = requests.get(
            SMARTY_ENDPOINT,
            params=params,
        )
        smarty_res = smarty_response.json()
        if not smarty_res:
            raise Exception(
                f"Could not get result back from Smarty - Response: {smarty_response.text}"
            )
        if "errors" in smarty_res:
            raise Exception(f"Got errors from Smarty - Errors: {json.dumps(smarty_res['errors'])}")

        return smarty_res[0]

    except Exception as e:
        raise Exception(
            {"message": f"Smarty Address Lookup Failure: {smarty_res}", "error": str(e)}
        )
