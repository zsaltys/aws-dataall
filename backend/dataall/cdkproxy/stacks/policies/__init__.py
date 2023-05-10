"""Contains the code for creating environment policies"""

from dataall.cdkproxy.stacks.policies import (
    _lambda, cloudformation, codestar, quicksight, redshift, stepfunctions, data_policy, service_policy
)

__all__ = ["_lambda", "cloudformation", "codestar", "quicksight",
           "redshift", "stepfunctions", "data_policy", "service_policy", "mlstudio"]