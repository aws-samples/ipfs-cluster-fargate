import aws_cdk as core
import aws_cdk.assertions as assertions

from ipfs_cluster.ipfs_cluster_fargate_stack import IpfsClusterFargateStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ipfs_cluster_fargate/ipfs_cluster_fargate_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = IpfsClusterFargateStack(app, "ipfs-cluster-fargate")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
