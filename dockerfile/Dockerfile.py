import re
import logging
import os
from .Directives import DockerfileDirectiveType
from .Parser import grammar
from .Parser import DockerfileVisitor
from parsimonious.exceptions import IncompleteParseError
from parsimonious.exceptions import VisitationError

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class NotDockerfileError(Error):
    pass


class EmptyFileError(Error):
    pass


class Dockerfile:

    def __init__(self, filename):
        self.directives = list()
        self.filename = filename
        try:
            with open(filename) as fp:
                self.dockerfile_content = self.normalize_content(fp.read())
                if len(self.dockerfile_content) == 0:
                    raise EmptyFileError
        except IsADirectoryError:
            logger.error(f"{filename} is a directory, expected a file.")
            raise NotDockerfileError
        except FileNotFoundError:
            logger.error(f"{filename} does not exist.")
            raise NotDockerfileError
        try:
            tree = grammar.parse(self.dockerfile_content)
        except IncompleteParseError:
            logger.error(f"Failed to parse file: {filename}")
            raise NotDockerfileError
        try:
            visitor = DockerfileVisitor(self)
        except VisitationError:
            logger.error(f"Error encountered while trying to visit the tree of instructions for: {filename}")
            raise NotDockerfileError
        # This populates all the directives
        visitor.visit(tree)

    def get_filename(self):
        return os.path.basename(self.filename)

    def add_directive(self, directive):
        self.directives.append(directive)

    def get_run_directives_last_stage(self):
        directives = self.directives.copy()
        directives.reverse()
        run_directives = list()
        for directive in directives:
            if directive.get()['type'] == str(DockerfileDirectiveType.RUN):
                run_directives.append(directive.get())
            if directive.get()['type'] == str(DockerfileDirectiveType.FROM):
                break
        return run_directives

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
            'run_last_stage': self.get_run_directives_last_stage()
        }
        return result

    def get_raw(self):
        result = [d.get() for d in self.directives]
        return result

    @staticmethod
    def normalize_content(dockerfile_content):
        # Remove comments
        comments = re.compile('#.*\n')
        normalized_content = comments.sub('', dockerfile_content)
        # Flatten lines
        line_continuation = re.compile('[\\\\][\n]+')
        normalized_content = line_continuation.sub(' ', normalized_content)
        spaces = re.compile('[ ]{2,}')
        normalized_content = spaces.sub(' ', normalized_content)
        empty_lines = re.compile('[\n]{2,}')
        normalized_content = empty_lines.sub('\n', normalized_content)
        return normalized_content.lstrip('\n')

    def get_maintainers(self):
        labels_dir = [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.LABEL)]
        maint_dir = [d.get() for d in self.directives if d.get()['type'] == str(DockerfileDirectiveType.MAINTAINER)]
        if len(maint_dir) > 0:
            return ', '.join(maint_dir[0]['maintainers'])
        else:
            for d in labels_dir:
                labels = d['labels']
                for l in labels:
                    for v in l.keys():
                        if v == "maintainer" or v == "MAINTAINER":
                            return l[v]
        return None
