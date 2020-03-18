from enum import Enum
import logging

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
            print(rule_type)

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
            registry = statement['registry']
            if registry not in self.allowed_registries:
                self.test_result.add_result(f"Registry {registry} is not an allowed registry to "
                                            f"pull images from",
                                            f"The FROM statement should be changed using images from one of the allowed"
                                            f" registries: {', '.join(self.allowed_registries)}", self.type,
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
            tag = statement['tag']
            if tag in self.forbidden_tags:
                self.test_result.add_result(f"Tag {tag} is not allowed",
                                            f"The FROM statements should be changed using an image with a fixed tag or "
                                            f"without any of the following tags: {', '.join(self.forbidden_tags)}",
                                            self.type, statement['raw_content'])

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
                                        "to run the application as a non-privileged user.",
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
