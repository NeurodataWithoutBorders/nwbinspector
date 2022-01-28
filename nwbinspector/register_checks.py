"""Authors: Cody Baker and Ben Dichter."""
from collections import defaultdict, OrderedDict
from functools import wraps

global available_checks
CRITICAL_IMPORTANCE = 2
BEST_PRACTICE_VIOLATION = 1
BEST_PRACTICE_SUGGESTION = 0

importance_levels = OrderedDict(
    CRITICAL_IMPORTANCE=CRITICAL_IMPORTANCE,
    BEST_PRACTICE_VIOLATION=BEST_PRACTICE_VIOLATION,
    BEST_PRACTICE_SUGGESTION=BEST_PRACTICE_SUGGESTION,
)
levels_to_importance = {v: k for k, v in importance_levels.items()}

HIGH_SEVERITY = 5
LOW_SEVERITY = 4
severity_levels = OrderedDict({"HIGH_SEVERITY": HIGH_SEVERITY, "LOW_SEVERITY": LOW_SEVERITY, None: 3})
levels_to_severity = {v: k for k, v in severity_levels.items()}

available_checks = OrderedDict({importance_level: defaultdict(list) for importance_level in importance_levels})


def register_check(importance, neurodata_type):
    """Wrap a check function to add it to the list of default checks for that severity and neurodata type."""

    def register_check_and_auto_parse(check_function):
        if importance not in importance_levels.values():
            raise ValueError(
                f"Indicated importance ({importance}) of custom check ({check_function.__name__}) is not a valid "
                "importance level! Please choose from [CRITICAL_IMPORTANCE, BEST_PRACTICE_VIOLATION, "
                "BEST_PRACTICE_SUGGESTION]."
            )
        check_function.importance = levels_to_importance[importance]
        check_function.neurodata_type = neurodata_type

        @wraps(check_function)
        def auto_parse_some_output(*args, **kwargs):
            if args:
                obj = args[0]
            else:
                obj = kwargs[list(kwargs)[0]]
            auto_parsed_result = check_function(*args, **kwargs)
            if auto_parsed_result is not None:
                auto_parsed_result.update(
                    importance=check_function.importance,
                    severity=levels_to_severity[auto_parsed_result.get("severity", severity_levels[None])],
                    check_function_name=check_function.__name__,
                    object_type=type(obj).__name__,
                    object_name=obj.name,
                )
            return auto_parsed_result

        available_checks[check_function.importance][check_function.neurodata_type].append(auto_parse_some_output)

        return auto_parse_some_output

    return register_check_and_auto_parse
