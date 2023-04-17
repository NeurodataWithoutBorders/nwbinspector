import os
from nwbinspector import available_checks

from collections import defaultdict


def gen_checks_by_importance():
    dd = defaultdict(list)

    for x in available_checks:
        dd[x.importance.name.replace("_", " ")].append(x)

    generate_checks_rst_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'checks_by_importance.rst')
    with open(generate_checks_rst_file, 'w') as f:
        f.write('''Checks by Importance
======================

This section lists the available checks organized by their importance level.

''')

        for importance_level, checks in dd.items():
            f.write(f'''{importance_level}
{'-' * (len(f'{importance_level}') + 1)}

''')

            for check in checks:
                f.write(f'*  :py:func:`~{check.__module__}.{check.__name__}` {check.__doc__}\n')

            f.write('\n')
