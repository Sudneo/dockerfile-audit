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
- [ ] Forbids tags
- [ ] Forbid root User
- [ ] Forbid Packages
- [ ] Forbid secrets
- [ ] Forbid lax chmod


ToDo:

- [X] Optimize Grammar, remove duplicate terminals and reduce the number of rules.
- [X] Implement comments parsing between RUN multiline commands.
- [X] Review RUN command parsing
- [X] FROM command breaks when registry has more than a "/"
- [X] LABEL sometimes breaks
- [ ] COPY --from options
- [X] FIX EXPOSE command

Eventual Features:

- [ ] Support $( ) arguments to commands (e.g., USER $(user:-user))
