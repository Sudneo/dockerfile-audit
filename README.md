# dockerfile-audit

Opinionated choices:

In order to greatly simplify the parsing, each Dockerfile is pre-processed before being parsed.
Preprocessing does the following actions:
* Removes comments
* Replaces line continuations (\ \n) with simple space
* Replaces multiple spaces with a single space
* Removes new lines at the beginning of the file

Implementation Roadmap

- [X] FROM
- [X] RUN
- [X] CMD
- [X] LABEL
- [X] MAINTAINER
- [X] EXPOSE
- [X] ENV
- [X] ADD
- [X] COPY
- [X] ENTRYPOINT
- [X] VOLUME
- [X] USER
- [X] WORKDIR
- [X] ARG
- [ ] ONBUILD
- [X] STOPSIGNAL
- [ ] HEALTHCHECK
- [X] SHELL
- [X] COMMENTS

Policy Roadmap

- [X] Enforce registries
- [X] Forbids tags
- [X] Forbid root User
- [X] Forbid privileged ports
- [X] Forbid Packages
- [X] Forbid secrets

General Improvements

- [ ] Parsing in stages could lead to better results. For example, first parse all ENV variables, replace
the value of the declared variables everywhere, and then proceed with parsing.
- [ ] RUN/CMD/ENTRYPOINTS command are harder to parse. If a package is installed and then removed, the search will
find 2 matches, while the package is correctly removed. Implementing RUN/CMD/ENTRYPOINT specific parsing might
allow to find out if package is installed and then removed.
- [ ] Use subprocess instead of os package

ToDo:

- [X] Optimize Grammar, remove duplicate terminals and reduce the number of rules.
- [X] Implement comments parsing between RUN multiline commands.
- [X] Review RUN command parsing
- [X] FROM command breaks when registry has more than a "/"
- [X] LABEL sometimes breaks
- [ ] COPY --from options
- [X] FIX EXPOSE command
- [ ] EXPOSE command, when used with $VARIABLE doesn't support /protocol syntax

Eventual Features:

- [ ] Support $( ) arguments to commands (e.g., USER $(user:-user))
