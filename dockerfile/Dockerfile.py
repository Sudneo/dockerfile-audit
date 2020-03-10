from .Directives import DockerfileDirectiveType


class Dockerfile:

    def __init__(self):
        self.directives = list()

    def add_directive(self, directive):
        self.directives.append(directive)

    def get_directives(self):
        result = {
            'from': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.FROM)],
            'user': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.USER)],
            'run': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.RUN)],
            'comments': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.COMMENT)],
            'labels': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.LABEL)],
            'expose': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.EXPOSE)],
            'maintainers': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.MAINTAINER)],
            'add': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.ADD)],
            'copy': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.COPY)],
            'env': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.ENV)],
            'cmd': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.CMD)],
            'entrypoint': [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.ENTRYPOINT)],
            'raw': [d.get() for d in self.directives]
        }
        return result
