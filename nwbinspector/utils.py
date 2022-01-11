"""Authors: Cody Baker and Ben Dichter."""
global default_checks
default_checks = {1: [], 2: [], 3: []}


def add_to_default_checks(severity: int):
    def decorator(check_function):
        if severity not in [1, 2, 3]:
            raise ValueError(
                f"Indicated severity ({severity}) of custom check ({check_function.__name__}) is not in range of 1-3."
            )
        default_checks[severity].append(check_function)
        return check_function

    return decorator
