import yaml
from .PolicyRule import *


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
            return {'failed-tests': test_results, 'audit-outcome': 'fail'}
        else:
            return {'audit-outcome': 'pass'}

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
