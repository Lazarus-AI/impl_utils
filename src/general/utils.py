def get_data_from_json_map(json_data, json_map):
    path = json_map.split(".")
    step = json_data
    for stone in path:
        if isinstance(step, list):
            step = step[0]

        step = step.get(stone)
        if step is None:
            break
    return step
