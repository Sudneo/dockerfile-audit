from enum import Enum
import logging
import re
import shlex

logger = logging.getLogger(__name__)


class PolicyRuleType(Enum):
    GENERIC_POLICY = 1
    ENFORCE_REGISTRY = 2
    FORBID_TAGS = 3
    FORBID_INSECURE_REGISTRIES = 4
    FORBID_ROOT = 5
    FORBID_PRIVILEGED_PORTS = 6
    FORBID_PACKAGES = 7
    FORBID_SECRETS = 8
    FORBID_LAX_CHMOD = 9


class PolicyFailedTestResult:

    def __init__(self):
        self.results = []

    def add_result(self, details, mitigations, rule_type, statement=None):
        try:
            self.results.append({'details': details, 'mitigations': mitigations, 'statement': statement,
                                 'type': rule_type.name})
        except AttributeError:
            logger.error(rule_type)

    def get_result(self):
        if len(self.results) > 0:
            return self.results
        else:
            return None


class PolicyRule:

    def __init__(self):
        self.type = PolicyRuleType.GENERIC_POLICY
        self.test_result = PolicyFailedTestResult()
        self.description = "Generic Policy Rule"
        pass

    def test(self, dockerfile_statements):
        pass

    def describe(self):
        return self.description

    def get_type(self):
        return self.type.name

    def details(self):
        pass


class EnforceRegistryPolicy(PolicyRule):

    def __init__(self, allowed_registries):
        super().__init__()
        self.description = "Allow images to be based (using the FROM command) only on images " \
                           "belonging to approved repositories."
        self.type = PolicyRuleType.ENFORCE_REGISTRY
        self.allowed_registries = allowed_registries

    def test(self, dockerfile_statements):
        self.test_result = PolicyFailedTestResult()
        from_statements = dockerfile_statements['from']
        for statement in from_statements:
            if statement['image'] == 'scratch':
                continue
            registry = statement['registry']
            # check if registry is a local_name for other FROM
            is_from_local_image = False
            for s in from_statements:
                if statement['image'] == s['local_name']:
                    is_from_local_image = True
            if not is_from_local_image:
                if registry not in self.allowed_registries:
                    self.test_result.add_result(f"Registry {registry} is not an allowed registry to "
                                                f"pull images from.",
                                                f"The FROM statement should be changed using images from one of the "
                                                f"allowed registries: {', '.join(self.allowed_registries)}", self.type,
                                                statement['raw_content'])
        return self.test_result.get_result()

    def details(self):
        return f"The following registries are allowed: {', '.join(self.allowed_registries)}."


class ForbidTags(PolicyRule):

    def __init__(self, forbidden_tags):
        super().__init__()
        self.description = "Restrict the use of certain tags for the images the" \
                           " build is sourced from (using FROM command)"
        self.type = PolicyRuleType.FORBID_TAGS
        self.forbidden_tags = forbidden_tags

    def test(self, dockerfile_statements):
        self.test_result = PolicyFailedTestResult()
        from_statements = dockerfile_statements['from']
        for statement in from_statements:
            if statement['image'] == 'scratch':
                continue
            tag = statement['tag']
            if tag in self.forbidden_tags:
                self.test_result.add_result(f"Tag {tag} is not allowed.",
                                            f"The FROM statements should be changed using an image with a fixed tag or "
                                            f"without any of the following tags: {', '.join(self.forbidden_tags)}",
                                            self.type, statement['raw_content'])
        return self.test_result.get_result()

    def details(self):
        return f"The following tags are forbidden: {', '.join(self.forbidden_tags)}."


class ForbidInsecureRegistries(PolicyRule):

    def __init__(self):
        super().__init__()
        self.description = "Forbid the use of HTTP protocol for the registries from which source images are stored."
        self.type = PolicyRuleType.FORBID_INSECURE_REGISTRIES

    def test(self, dockerfile_statements):
        self.test_result = PolicyFailedTestResult()
        from_statements = dockerfile_statements['from']
        for statement in from_statements:
            registry = statement['registry']
            if registry.startswith('http://'):
                self.test_result.add_result(f"Registry {registry} uses HTTP and therefore it is considered insecure",
                                            f"The FROM statement should be changed using images from a registry which"
                                            f"uses HTTPs.", self.type, statement['raw_content'])
        return self.test_result.get_result()


class ForbidRoot(PolicyRule):

    def __init__(self):
        super().__init__()
        self.description = "Forbid the container to run as a privileged (root) user."
        self.type = PolicyRuleType.FORBID_ROOT

    def test(self, dockerfile_statements):
        self.test_result = PolicyFailedTestResult()
        user_statements = dockerfile_statements['user']
        if len(user_statements) == 0:
            self.test_result.add_result("No USER statements found. By default, if privileges are not dropped, the "
                                        "container will run as root.",
                                        "Create a user and add a USER statement before the entrypoint of the image"
                                        " to run the application as a non-privileged user.",
                                        self.type, statement=None)
        else:
            last_user = user_statements[-1]['user']
            if last_user == "0" or last_user == "root":
                self.test_result.add_result("The last USER statement found elevates privileged to root.",
                                            "Add one more USER statement before the entrypoint of the image"
                                            "to run the application as a non-privileged user.", self.type,
                                            user_statements[-1]['raw_content'])
        return self.test_result.get_result()


class ForbidPrivilegedPorts(PolicyRule):

    def __init__(self):
        super().__init__()
        self.description = "Forbid the image to expose privileged ports that require administrative permissions."
        self.type = PolicyRuleType.FORBID_PRIVILEGED_PORTS

    def test(self, dockerfile_statements):
        self.test_result = PolicyFailedTestResult()
        expose_statements = dockerfile_statements['expose']
        for statement in expose_statements:
            for port in statement['ports']:
                try:
                    if int(port['port']) <= 1024:
                        self.test_result.add_result(f"The container exposes a privileged port: {port}. Privileged ports"
                                                    f" require the application which uses it to run as root.",
                                                    "Change the configuration for the application to bind on a port "
                                                    "greater than 1024, and change the Dockerfile to reflect this "
                                                    "modification.",
                                                    self.type, statement['raw_content'])
                except ValueError:
                    port_number = self.__get_port_from_env(port['port'], dockerfile_statements)
                    if port_number is not None:
                        if int(port_number) <= 1024:
                            self.test_result.add_result(
                                f"The container exposes a privileged port: {port_number}. Privileged ports "
                                f"require the application which uses it to run as root.",
                                "Change the configuration for the application to bind on a port greater"
                                "than 1024, and change the Dockerfile to reflect this modification.",
                                self.type, statement['raw_content'])

        return self.test_result.get_result()

    @staticmethod
    def __get_port_from_env(env_name, dockerfile_statements):
        env_statements = dockerfile_statements['env']
        for statement in env_statements:
            variables = statement['variables']
            for v in variables:
                if env_name in v.keys():
                    return v[env_name]
        return None


class ForbidPackages(PolicyRule):

    def __init__(self, forbidden_packages):
        super().__init__()
        self.description = "Forbid the installation/use of dangerous packages."
        self.type = PolicyRuleType.FORBID_PACKAGES
        self.forbidden_packages = forbidden_packages

    def test(self, dockerfile_statements):
        self.test_result = PolicyFailedTestResult()
        run_statements = dockerfile_statements['run']
        entrypoint_statements = dockerfile_statements['entrypoint']
        cmd_statements = dockerfile_statements['cmd']
        commands = self.__split_single_commands(dockerfile_statements['run_last_stage'])
        installed_packages = self.__get_installed_packages(commands)
        if len(installed_packages) == 0:
            logger.warning(f"No automated package install detection. Falling back on dumb detection.")
            for statement in entrypoint_statements+run_statements+cmd_statements:
                for package in self.forbidden_packages:
                    package_regex = re.compile(f"(^|[^a-zA-Z0-9]){package}([^a-zA-Z0-9]|$)")
                    match = package_regex.search(statement['raw_content'])
                    if match is not None:
                        self.test_result.add_result(f"Forbidden package \"{package}\" is installed or used.",
                                                    f"The RUN/CMD/ENTRYPOINT statement should be reviewed and package"
                                                    f" \"{package}\" should be removed unless absolutely necessary.",
                                                    self.type, statement['raw_content'])
        else:
            logger.debug(f"Found the following installed packages: {installed_packages}")
            for package in self.forbidden_packages:
                if package in installed_packages:
                    self.test_result.add_result(f"Forbidden package \"{package}\" is installed.",
                                                f"The RUN statements should be reviewed and package"
                                                f" \"{package}\" should be removed unless absolutely necessary.",
                                                self.type, None)
        return self.test_result.get_result()

    @staticmethod
    def __get_installed_packages(commands):
        package_manager_commands = {'apt-get': {'install': ['install'], 'remove': ['remove', 'purge']},
                                    'apt': {'install': ['install'], 'remove': ['remove', 'purge']},
                                    'dnf': {'install': ['install'], 'remove': ['remove', 'autoremove']},
                                    'yum': {'install': ['install'], 'remove': ['remove', 'erase', 'autoremove']},
                                    'apk': {'install': ['add'], 'remove': ['del']}}
        flag_regex = re.compile("^[-]{1,2}[\\S]+$")
        packages_installed = list()
        packages_removed = list()
        # For every command
        for command in commands:
            # For every token in the command
            for i in range(len(command)):
                # If token at index i is not a package manager key, continue
                if command[i] not in package_manager_commands.keys():
                    continue
                # If token at index i is a package manager key
                else:
                    # key = package-manager name
                    key = command[i]
                    # For every word after the package manager key
                    for k in range(len(command[i+1:])):
                        next_command = command[i+1+k]
                        # If a word starts with - or -- ignore it
                        if flag_regex.match(next_command):
                            continue
                        # If a word is an 'install' command for that package manager
                        elif next_command in package_manager_commands[key]['install']:
                            # Add to packages installed every word after it
                            packages_installed += command[i+1+k+1:]
                            break
                        # If a word is a 'remove' command for that package manager
                        elif next_command in package_manager_commands[key]['remove']:
                            packages_removed += command[i+1+k+1:]
                            break
                    break
        final_packages = [p for p in packages_installed if p not in packages_removed and not flag_regex.match(p)]
        return final_packages

    @staticmethod
    def __split_single_commands(run_directives):
        commands = list()
        for directive in run_directives:
            subcommand = list()
            try:
                parsed = shlex.split(directive['raw_content'])
            except ValueError:
                break
            for word in parsed:
                if word in ['&', '&&', '|', '||', ';']:
                    commands.append(subcommand)
                    subcommand = list()
                else:
                    subcommand.append(word)
            commands.append(subcommand)
        return commands

    def details(self):
        return f"The following packages are forbidden: {', '.join(self.forbidden_packages)}."


class ForbidSecrets(PolicyRule):

    def __init__(self, secrets_patterns, allowed_patterns):
        super().__init__()
        self.description = "Forbid the inclusion of secrets in the image."
        self.type = PolicyRuleType.FORBID_SECRETS
        self.secrets_patterns = secrets_patterns
        self.allowed_patterns = allowed_patterns

    def test(self, dockerfile_statements):
        self.test_result = PolicyFailedTestResult()
        add_statement = dockerfile_statements['add']
        copy_statements = dockerfile_statements['copy']
        for statement in add_statement+copy_statements:
            for source in statement['source']:
                is_forbidden, pattern = self.__is_forbidden_pattern(source)
                if is_forbidden and not self.__is_whitelisted_pattern(source):
                    self.test_result.add_result(f"Forbidden file matching pattern \"{pattern}\" is added into "
                                                f"the image.",
                                                f"The ADD/COPY statement should be changed or removed. Secrets"
                                                f" should be provisioned using a safer and stateless way (Vault,"
                                                f" Kubernetes secrets) instead.",
                                                self.type, statement['raw_content'])
        return self.test_result.get_result()

    def __is_forbidden_pattern(self, string):
        for pattern in self.secrets_patterns:
            secret_regex = re.compile(pattern)
            match_source = secret_regex.search(string)
            if match_source is not None:
                return True, pattern
        return False, None

    def __is_whitelisted_pattern(self, string):
        for p in self.allowed_patterns:
            allowed_regex = re.compile(p)
            match_allowed = allowed_regex.search(string)
            if match_allowed is not None:
                return True
        return False

    def details(self):
        return f"The following patterns are forbidden: {', '.join(self.secrets_patterns)}.\n" \
               f"The following patterns are whitelisted: {', '.join(self.allowed_patterns)}"
