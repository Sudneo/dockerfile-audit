from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DockerfileDirectiveType(Enum):
    FROM = 1
    RUN = 2
    CMD = 3
    LABEL = 4
    MAINTAINER = 5
    EXPOSE = 6
    ENV = 7
    ADD = 8
    COPY = 9
    ENTRYPOINT = 10
    VOLUME = 11
    USER = 12
    WORKDIR = 13
    ARG = 14
    ONBUILD = 15
    STOPSIGNAL = 16
    HEALTHCHECK = 17
    SHELL = 18
    COMMENT = 19

    def __str__(self):
        return self.name


class DockerfileDirective:

    def __init__(self, directive_type, raw_content):
        self.type = directive_type
        self.content = raw_content

    def get(self):
        return {'type': str(self.type), 'raw_content': self.content}


class FromDirective(DockerfileDirective):

    def __init__(self, raw_content):
        self.platform = None
        self.registry = None
        self.image_local_name = None
        self.image_tag = None
        data = raw_content['content']
        try:
            self.platform = data['platform']
        except KeyError:
            logger.info(f"Platform field missing.")
            pass
        try:
            self.registry = data['registry']
        except KeyError:
            logger.warning(f"Registry field missing.")
            pass
        try:
            self.image_local_name = data['local_name']
        except KeyError:
            logger.info(f"Local Name field missing.")
            pass
        try:
            self.image_tag = data['tag']
        except KeyError:
            logger.warning(f"Tag field missing.")
            pass

        try:
            self.image_name = data['image']
        except KeyError as error:
            logger.error("Image name is a mandatory field for a FROM directive.")
            logger.error(error)
            pass
        super().__init__(DockerfileDirectiveType.FROM, raw_content['raw_command'])

    def get(self):
        return {
            'type': str(self.type),
            'raw_content': self.content,
            'registry': self.registry,
            'image': self.image_name,
            'tag': self.image_tag,
            'local_name': self.image_local_name or None
        }


class RunDirective(DockerfileDirective):

    def __init__(self, raw_content):
        super().__init__(DockerfileDirectiveType.RUN, raw_content['content'])


class LabelDirective(DockerfileDirective):

    def __init__(self, raw_content):
        self.labels = raw_content['content']
        super().__init__(DockerfileDirectiveType.LABEL, raw_content['raw_command'])

    def get(self):
        return {
            'type': str(self.type),
            'raw_content': self.content,
            'labels': self.labels
        }


class UserDirective(DockerfileDirective):

    def __init__(self, raw_content):
        data = raw_content['content']
        try:
            self.user = data['user']
        except KeyError as error:
            logger.error(f"User field is mandatory.\n{error}")
        try:
            self.group = data['group']
        except KeyError as error:
            logger.warning(f"Group field missing.\n{error}")
            pass
        super().__init__(DockerfileDirectiveType.USER, raw_content['raw_command'])

    def get(self):
        return {
            'type': str(self.type),
            'user': self.user,
            'group': self.group,
            'raw_content': self.content
                }


class ExposeDirective(DockerfileDirective):

    def __init__(self, raw_content):
        self.ports = raw_content['content']
        super().__init__(DockerfileDirectiveType.EXPOSE, raw_content['raw_command'])

    def get(self):
        return {
            'type': str(self.type),
            'raw_content': self.content,
            'ports': self.ports
        }


class MaintainerDirective(DockerfileDirective):

    def __init__(self, raw_content):
        self.maintainers = raw_content['content']
        super().__init__(DockerfileDirectiveType.MAINTAINER, raw_content['raw_command'])

    def get(self):
        return {
            'type': str(self.type),
            'raw_content': self.content,
            'maintainers': self.maintainers
        }


class AddDirective(DockerfileDirective):

    def __init__(self, raw_content):
        self.chown = raw_content['content']['chown']
        self.source = raw_content['content']['source']
        self.destination = raw_content['content']['destination']
        super().__init__(DockerfileDirectiveType.ADD, raw_content['raw_command'])

    def get(self):
        return {
            'type': str(self.type),
            'raw_content': self.content,
            'chown': self.chown,
            'source': self.source,
            'destination': self.destination
        }


class CopyDirective(DockerfileDirective):

    def __init__(self, raw_content):
        self.chown = raw_content['content']['chown']
        self.source = raw_content['content']['source']
        self.destination = raw_content['content']['destination']
        super().__init__(DockerfileDirectiveType.COPY, raw_content['raw_command'])

    def get(self):
        return {
            'type': str(self.type),
            'raw_content': self.content,
            'chown': self.chown,
            'source': self.source,
            'destination': self.destination
        }


class EnvDirective(DockerfileDirective):

    def __init__(self, raw_content):
        self.variables = raw_content['content']
        super().__init__(DockerfileDirectiveType.ENV, raw_content['raw_command'])

    def get(self):
        return {
            'type': str(self.type),
            'raw_content': self.content,
            'variables': self.variables
        }


class CmdDirective(DockerfileDirective):

    def __init__(self, raw_content):
        super().__init__(DockerfileDirectiveType.CMD, raw_content['content'])


class EntrypointDirective(DockerfileDirective):

    def __init__(self, raw_content):
        super().__init__(DockerfileDirectiveType.ENTRYPOINT, raw_content['content'])


class Comment(DockerfileDirective):

    def __init__(self, raw_content):
        super().__init__(DockerfileDirectiveType.COMMENT, raw_content)
