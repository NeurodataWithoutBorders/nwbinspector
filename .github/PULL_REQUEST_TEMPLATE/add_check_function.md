---
name: Add New Check Function
about: Add code that applies a new check function to NWBFiles and their contents. 
title: "[Add Check]: "
labels: new check
---

## Motivation

What was the reasoning behind this check? Please explain the changes briefly.

## Checklist

- [ ] If this PR fixes an issue, is the first line of the PR description `fix #XX` where `XX` is the issue number?
- [ ] Are you adding only a single new check function? If you want to add more than one, please consider separating them into multiple Pull Requests to make review as quick and easy as possible.
- [ ] Have you registered the check using the `register_check` decorator and associated `importance` level?
- [ ] Have you included a simple, one-line docstring (or longer, if there are optional arguments). Must conform with [numpy docstring style](https://numpydoc.readthedocs.io/en/latest/format.html) as well as [pydocstyle](http://www.pydocstyle.org/en/stable/).
- [ ] Have you simplified the logic of the check function as much as possible?
- [ ] Have you added at least one positive (check returns None) and one negative (check returns intended `InspectorMessage`) test for the new check function?
- [ ] Have you ensured the PR description clearly describes the problem and solutions?
- [ ] Have you checked to ensure that there aren't other open or previously closed [Pull Requests](https://github.com/neurodatawithoutborders/nwbinspector/pulls) for the same change?
