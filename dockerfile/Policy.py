import yaml
from .PolicyRule import *

logger = logging.getLogger(__name__)


class DockerfilePolicy(object):

    def __init__(self, policy_file):
        self.policy_rules = list()
        self.policy_file = policy_file
        self.init_rules()

    def evaluate_dockerfile(self, dockerfile_object):
        test_results = list()
        for policy_rule in self.policy_rules:
            test_rule_result = policy_rule.test(dockerfile_object.get_directives())
            if test_rule_result is not None:
                test_results.append(test_rule_result)
        if len(test_results) > 0:
            return {'failed-tests': test_results, 'audit-outcome': 'fail', 'filename': dockerfile_object.get_filename(),
                    'maintainers': dockerfile_object.get_maintainers()}
        else:
            return {'audit-outcome': 'pass', 'filename': dockerfile_object.get_filename(),
                    'maintainers': dockerfile_object.get_maintainers()}

    def init_rules(self):
        try:
            with open(self.policy_file) as file:
                try:
                    policy_rules = yaml.safe_load(file)
                except yaml.YAMLError:
                    logger.error(f"Failed to parse {self.policy_file}: not a valid yaml file.")
                    raise TypeError
        except FileNotFoundError:
            logger.error(f"Policy file {self.policy_file} does not exist.")
            raise FileNotFoundError
        policies = policy_rules['policy']
        try:
            enforce_registries = policies['enforce_authorized_registries']
            if enforce_registries['enabled']:
                self.policy_rules.append(EnforceRegistryPolicy(enforce_registries['registries']))
        except KeyError:
            logger.debug("No enforce_authorized_registries found in policy, skipping.")
        try:
            forbid_tags = policies['forbid_floating_tags']
            if forbid_tags['enabled']:
                self.policy_rules.append(ForbidTags(forbid_tags['forbidden_tags']))
        except KeyError:
            logger.debug("No forbid_floating_tags found in policy, skipping.")
        try:
            forbid_insecure_registries = policies['forbid_insecure_registries']
            if forbid_insecure_registries['enabled']:
                self.policy_rules.append(ForbidInsecureRegistries())
        except KeyError:
            logger.debug("No forbid_insecure_registries found in policy, skipping.")
        try:
            forbid_root = policies['forbid_root']
            if forbid_root['enabled']:
                self.policy_rules.append(ForbidRoot())
        except KeyError:
            logger.debug("No forbid_root found in policy, skipping.")
        try:
            forbid_privileged_ports = policies['forbid_privileged_ports']
            if forbid_privileged_ports['enabled']:
                self.policy_rules.append(ForbidPrivilegedPorts())
        except KeyError:
            logger.debug("No forbid_privileged_ports found in policy, skipping.")
        try:
            forbid_packages = policies['forbid_packages']
            if forbid_packages['enabled']:
                self.policy_rules.append(ForbidPackages(forbid_packages['forbidden_packages']))
        except KeyError:
            logger.debug("No forbid_packages found in policy, skipping.")
        try:
            forbid_secrets = policies['forbid_secrets']
            if forbid_secrets['enabled']:
                try:
                    forbid_patterns = forbid_secrets['secrets_patterns']
                    try:
                        allowed_patterns = forbid_secrets['allowed_patterns']
                    except KeyError:
                        allowed_patterns = []
                        pass
                    if len(forbid_patterns) == 0:
                        logger.debug("secrets_patterns defined but with an empty list. Skipping.")
                    else:
                        self.policy_rules.append(ForbidSecrets(forbid_patterns, allowed_patterns))
                except KeyError:
                    logger.error('forbid_secrets rule added but not secrets_patterns defined.')
        except KeyError:
            logger.debug("No forbid_secrets found in policy, skipping.")

    def get_policy_rules_enabled(self):
        enabled_rules = list()
        for rule in self.policy_rules:
            rule_details = rule.details()
            if rule_details is None:
                rule_details = ""
            enabled_rules.append({'type': rule.get_type(), 'description': rule.describe(),
                                  'details': rule_details})
        return enabled_rules
