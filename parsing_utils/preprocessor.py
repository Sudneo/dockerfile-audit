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

    # def __get_env_keyvalue(self):
    #     dockerfile_lines = self.content.split('\n')
    #     env_match = re.compile('^(env|ENV) .*')
    #     backslash_space = re.compile('\\ ')
    #     line_with_keyvalues = re.compile('(env|ENV) (([ ]?(?P<key>[^=\\s\'\"]+|\"[^=]+\"|\'[^=]\')=(?P<value>[^=\\s\'
    #                                      '\"]+|\"[^=]+\"|\'[^=]\'))+)')
    #     for line in dockerfile_lines:
    #         if env_match.match(line):
    #             backslash_space.sub('#', line)
    #             if line_with_keyvalues.match(line):
    #                 print(f"match: {line}")


