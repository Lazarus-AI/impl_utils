from typing import Any

from external_apis.consensus_apis import ping_npi


def validate_npi_using_npi_registry(npi: str) -> Any:
    """
    Ping the NPI Registry to get information for a given NPI number.

    Parameters:
    npi (str): The NPI number to query.

    Returns:
    dict: A dictionary containing the response from the NPI Registry.
    """
    return ping_npi(npi)
