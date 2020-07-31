from dockerfile import Dockerfile


class DockerfileAuditor:

    def __init__(self, policy):
        self.policy = policy

    def audit(self, file_name):
        try:
            dockerfile_object = Dockerfile.Dockerfile(file_name)
        except (Dockerfile.NotDockerfileError, Dockerfile.EmptyFileError):
            return []
        policy_result = self.policy.evaluate_dockerfile(dockerfile_object)
        return policy_result

