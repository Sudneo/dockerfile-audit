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

    def add_result(self, details, mitigations, rule_type):
        self.results.append({'details': details, 'mitigations': mitigations, 'type': rule_type})

    def get_result(self):
        return self.results


class PolicyRule:

    def __init__(self):
        self.type = PolicyRuleType.GENERIC_POLICY
        self.test_result = PolicyFailedTestResult()
        pass

    def test(self, dockerfile_statements):
        pass


class EnforceRegistryPolicy(PolicyRule):

    def __init__(self, allowed_registries):
        super().__init__()
        self.type = PolicyRuleType.ENFORCE_REGISTRY
        self.allowed_registries = allowed_registries

    def test(self, dockerfile_statements):
        from_statements = dockerfile_statements['from']
        for statement in from_statements:
            registry = statement['registry']
            if registry not in self.allowed_registries:
                self.test_result.add_result(f"Registry {registry} is not an allowed registry to "
                                            f"pull images from",
                                            f"The FROM statement should be changed using images from one of the allowed"
                                            f"registries: {', '.join(self.allowed_registries)}", str(self.type))
        return self.test_result.get_result()
