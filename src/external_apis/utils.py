from typing import Any

from external_apis.consensus_apis import get_npi_registry


def validate_npi(npi: str) -> Any:
    """
    Ping the NPI Registry to get information for a given NPI number.

    Parameters:
    npi (str): The NPI number to query.

    Returns:
    dict: A dictionary containing the response from the NPI Registry.
    """
    return get_npi_registry(npi)
