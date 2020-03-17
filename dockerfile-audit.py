import os
from dockerfile import Dockerfile
from dockerfile import Policy

policy = Policy.DockerfilePolicy('policy-example.yaml')
dockerfiles = os.listdir('dockerfiles')
for file in dockerfiles:
    d = Dockerfile.Dockerfile(f"/home/daniele/dev/dockerfile-audit/dockerfiles/{file}")
    policy_result = policy.evaluate_dockerfile(d)
    print(policy_result)