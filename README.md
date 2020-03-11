# dockerfile-audit

Opinionated choices:

* At the moment the comments work, but not if they are in between multiline commands (e.g, LABEL or RUN).
* The easiest way to get a good result is to strip comments before parsing:

```python
    with open('Dockerfile-test') as f:
        data = f.read()
        data_no_comments = list()
        lines = data.split('\n')
        for line in lines:
            if len(line.lstrip(' ')) > 0:
                if line.lstrip(' ')[0] != "#":
                    data_no_comments.append(line)
        dockerfile = '\n'.join(data_no_comments)
        tree = grammar.parse(dockerfile)
        iv = IniVisitor()
        output = iv.visit(tree)
```

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

ToDo:

- [ ] Implement comments parsing between RUN multiline commands

Eventual Features:

- [ ] Support $( ) arguments to commands (e.g., USER $(user:-user))
