#!/usr/bin/env python3
import os

import aws_cdk as cdk

from ipfs_cluster.ipfs_cluster_fargate_stack import IpfsClusterFargateStack

from dotenv import dotenv_values

IPFS_CLUSTER_ENV_FILE = 'ipfscluster.env'

app = cdk.App()
IpfsClusterFargateStack(app, "IpfsClusterFargateStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.
    ipfs_cluster_env = dotenv_values(dotenv_path=IPFS_CLUSTER_ENV_FILE),
    env=cdk.Environment(
        account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
        region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
    ),
    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()
