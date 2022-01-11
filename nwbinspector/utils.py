"""Authors: Cody Baker and Ben Dichter."""
global default_checks
default_checks = {1: dict(), 2: dict(), 3: dict()}


def add_to_default_checks(severity: int, data_object):
    def decorator(check_function):
        if severity not in [1, 2, 3]:
            raise ValueError(
                f"Indicated severity ({severity}) of custom check ({check_function.__name__}) is not in range of 1-3."
            )
        if data_object not in default_checks[severity]:
            default_checks[severity].update({data_object: []})
        default_checks[severity][data_object].append(check_function)
        return check_function

    return decorator
