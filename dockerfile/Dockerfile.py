from .Directives import DockerfileDirectiveType
from .Parser import grammar
from .Parser import DockerfileVisitor


class Dockerfile:

    def __init__(self):
        # Add file as argument and preprocessing
        # Preprocessing should remove comments and also flatten lines into single line
        self.directives = list()

    def add_directive(self, directive):
        self.directives.append(directive)

    def get_directives(self):
        result = {
            'from': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.FROM)],
            'user': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.USER)],
            'run': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.RUN)],
            'labels': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.LABEL)],
            'expose': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.EXPOSE)],
            'maintainers': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.MAINTAINER)],
            'add': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.ADD)],
            'copy': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.COPY)],
            'env': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.ENV)],
            'cmd': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.CMD)],
            'entrypoint': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.ENTRYPOINT)],
            'workdir': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.WORKDIR)],
            'volume': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.VOLUME)],
            'shell': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.SHELL)],
            'stopsignal': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.STOPSIGNAL)],
            'arg': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.ARG)],
        }
        return result

    def get_raw(self):
        result = [d.get() for d in self.directives]
        return result
