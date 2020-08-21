import logging
import re

logger = logging.getLogger(__name__)


class DockerfilePreprocessor:

    def __init__(self, dockerfile_content):
        self.content = dockerfile_content

    def get_normalized_content(self):
        self.__normalize()
        return self.content

    def __normalize(self):
        self.__flatten_lines()
        self.__remove_comments()
        self.__remove_double_whitespaces()
        self.__remove_empty_lines()
        self.__removes_leading_newlines()
        self.__removes_leading_spaces()
        self.__removes_trailing_spaces()
        envs = self.__get_env_basic()
        self.__resolve_envs(envs)
        envs = self.__get_env_keyvalue()
        self.__resolve_envs(envs)

    def __resolve_envs(self, envs):
        for key, value in envs.items():
            env_names = [f"[$]{key}", f"[$]{{{key}(-[\\S]+)?}}"]
            for pattern in env_names:
                regex = re.compile(pattern)
                if regex.search(self.content):
                    logger.debug(f"Resolving env variable {key} with value {value}.")
                self.content = regex.sub(value, self.content)

    def __remove_comments(self):
        comments = re.compile('#.*\n')
        self.content = comments.sub('', self.content)

    def __flatten_lines(self):
        line_continuation = re.compile('[\\\\][\n]+')
        self.content = line_continuation.sub(' ', self.content)

    def __remove_double_whitespaces(self):
        spaces = re.compile('[ ]{2,}')
        self.content = spaces.sub(' ', self.content)

    def __remove_empty_lines(self):
        empty_lines = re.compile('[\n]{2,}')
        self.content = empty_lines.sub('\n', self.content)

    def __removes_leading_spaces(self):
        self.content = self.content.lstrip(' ')
        lines_with_spaces = re.compile('\n[ ]+')
        self.content = lines_with_spaces.sub('\n', self.content)

    def __removes_trailing_spaces(self):
        ending_whitespaces = re.compile('[ ]+\n')
        self.content = ending_whitespaces.sub('\n', self.content)

    def __removes_leading_newlines(self):
        self.content = self.content.lstrip('\n')

    def __get_env_basic(self):
        envs = dict()
        assignment = re.compile('(env|ENV) (?P<key>["\'\\S]+) (?P<value>[\'"\\S]+)')
        matches = assignment.findall(self.content)
        for match in matches:
            _, key, value = match
            envs[key] = value
        return envs

    @staticmethod
    def __replace_spaces_in_quotes(line):
        inside = False
        index = 0
        while index < len(line):
            if not inside and (line[index] == "'" or line[index] == '"'):
                inside = True
            elif inside and line[index] == " ":
                line = line[:index] + "#" + line[index + 1:]
            elif inside and (line[index] == "'" or line[index] == '"'):
                inside = False
            index += 1
        return line

    def __get_env_keyvalue(self):
        variables = dict()
        dockerfile_lines = self.content.split('\n')
        env_match = re.compile('^(env|ENV) .*')
        line_with_keyvalues = re.compile('(env|ENV) ((([^=\\s]+|(\"|\')[^\'\"=]+(\"|\'))=([^=\\s\"\']+|(\"|\')'
                                         '[^=\"\']+(\"|\')[ ]*))+)')
        for line in dockerfile_lines:
            if env_match.match(line):
                if line_with_keyvalues.match(line):
                    logger.debug(f"Key value ENV match: {line}")
                    line = re.sub('\\\\ ', '#', line)
                    line = self.__replace_spaces_in_quotes(line)
                    envs = line.split(" ")[1:]
                    for env in envs:
                        variables[env.split("=")[0]] = env.split("=")[1].replace("\"", "").\
                            replace("'", "").\
                            replace("#", " ")
        return variables






