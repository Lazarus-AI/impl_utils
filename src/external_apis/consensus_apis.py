from typing import Any

import requests


def get_npi_registry(npi: str) -> Any:
    """
    Ping the NPI Registry to get information for a given NPI number.

    Parameters:
    npi (str): The NPI number to query.

    Returns:
    dict: A dictionary containing the response from the NPI Registry.
    """
    url = f"https://npiregistry.cms.hhs.gov/api/?number={npi}&pretty=&version=2.1"
    resp = requests.get(url).json()
    return resp
