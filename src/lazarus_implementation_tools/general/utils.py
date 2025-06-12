def get_data_from_json_map(json_data, json_map):
    """Retrieves data from a nested JSON structure using a dot-separated path.

    :param json_data: The nested JSON data.
    :param json_map: A dot-separated string representing the path to the desired data.

    :returns: The data at the specified path, or None if the path is invalid.

    """
    path = json_map.split(".")
    step = json_data
    for stone in path:
        if isinstance(step, list):
            step = step[0]

        step = step.get(stone)
        if step is None:
            break
    return step
