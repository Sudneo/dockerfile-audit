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
            'raw': [d.get() for d in self.directives]
        }
        return result
