"""Authors: Cody Baker and Ben Dichter."""
global default_checks
default_checks = {1: [], 2: [], 3: []}


def add_to_default_checks(severity: int):
    def decorator(check_function):
        default_checks[1].append(check_function)
        return check_function

    return decorator
