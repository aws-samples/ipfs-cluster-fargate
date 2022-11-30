import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_efs as efs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_servicediscovery as cloudmap,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_secretsmanager as secretsmanager,
    SecretValue,
)
from constructs import Construct

import boto3


def get_cloudfront_prefix_id(region_name) -> str:
    client = boto3.client('ec2', region_name=region_name)
    resp = client.describe_managed_prefix_lists(
        Filters=[
            {
                'Name': 'prefix-list-name',
                'Values': ['com.amazonaws.global.cloudfront.origin-facing']
            },
            {
                'Name': 'owner-id',
                'Values': ['AWS']
            }
        ]
    )
    return resp['PrefixLists'][0]['PrefixListId']


class IpfsClusterFargateStack(Stack):

    def __init__(self, scope: Construct,
                 construct_id: str,
                 ipfs_cluster_env: dict, **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        self._define_parameter()

        _cf_prefix_list_id = get_cloudfront_prefix_id(self.region)

        # Create A VPC with 3 public subnet on 3 diff AZs
        _vpc = ec2.Vpc(
            self, "IpfsFargateVpc",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name='public',
                    subnet_type=ec2.SubnetType.PUBLIC
                )
            ],
            max_azs=3
        )

        # Create Secret in AWS Secret Manager
        _ipfs_cluster_api_credential = ecs.Secret.from_secrets_manager(
            secretsmanager.Secret(self,
                                  'SMClusterApiCredential',
                                  description=f'{cdk.Aws.STACK_NAME} Credential',
                                  secret_name=f'{cdk.Aws.STACK_NAME}-IPFS-Cluster-Credential',
                                  secret_string_value=SecretValue.cfn_parameter(
                                      self._parameter_ipfs_cluster_api_credential
                                  )
                                  ))

        _ipfs_cluster_secret = ecs.Secret.from_secrets_manager(
            secretsmanager.Secret(self, 'SMClusterSecret',
                                  description=f'{cdk.Aws.STACK_NAME} IPFS Cluster Secret',
                                  secret_name=f'{cdk.Aws.STACK_NAME}-ClusterSecret',
                                  secret_string_value=SecretValue.cfn_parameter(
                                      self._parameter_ipfs_cluster_secret
                                  )
                                  ))

        _ipfs_cluster_private_key = ecs.Secret.from_secrets_manager(
            secretsmanager.Secret(self, 'SMPrivateKey',
                                  description=f'{cdk.Aws.STACK_NAME} IPFS Cluster Private Key',
                                  secret_name=f'{cdk.Aws.STACK_NAME}-PrivateKey',
                                  secret_string_value=SecretValue.cfn_parameter(
                                      self._parameter_ipfs_cluster_private_key
                                  )
                                  ))

        _ipfs_cluster_id = self._parameter_ipfs_cluster_id.value_as_string

        # Create ECS Cluster
        _ecs_cluster = ecs.Cluster(self, "IpfsEcsCluster", vpc=_vpc)

        # ALB for IPFS Cluster
        _alb_ipfs_cluster_sg = ec2.SecurityGroup(self, 'AlbIpfsClusterSecurityGroup',
                                                 allow_all_outbound=False,
                                                 vpc=_vpc,
                                                 description='Inbound/Outbound rules for the ALB in front of IPFS Cluster REST API'
                                                 )

        _alb_ipfs_cluster_sg.add_egress_rule(
            peer=ec2.Peer.ipv4(_vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(9094),
            description='Allow connection out to the IPFS Cluster REST API '
            ' on port 9094 anywhere in internal network'
        )

        _alb_ipfs_cluster_sg.add_egress_rule(
            peer=ec2.Peer.ipv4(_vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(8080),
            description='Allow connection out to the IPFS Gateway '
            ' on port 8080 anywhere in internal network'
        )

        _alb_ipfs_cluster_sg.add_ingress_rule(
            peer=ec2.Peer.prefix_list(_cf_prefix_list_id),
            connection=ec2.Port.all_tcp(),
            description='Allow incoming traffic from Cloudfront'
        )

        _alb_ipfs_cluster = elbv2.ApplicationLoadBalancer(
            self, 'AlbIpfsCluster',
            vpc=_vpc,
            internet_facing=True,
            security_group=_alb_ipfs_cluster_sg
        )

        _alb_ipfs_cluster_target_group = elbv2.ApplicationTargetGroup(
            self, "AlbIpfsClusterTargetGroup",
            target_type=elbv2.TargetType.IP,
            port=9094,
            protocol=elbv2.ApplicationProtocol.HTTP,
            health_check=elbv2.HealthCheck(
                enabled=True,
                path='/id',
                healthy_http_codes='401',
            ),
            vpc=_vpc
        )

        _alb_ipfs_cluster_listener = _alb_ipfs_cluster.add_listener(
            'AlbIpfsClusterListner',
            port=9094,
            open=False,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_target_groups=[_alb_ipfs_cluster_target_group]
        )

        # Security Group for EFS to allow access from IPFS Fargate Service
        _efs_sg = ec2.SecurityGroup(self, 'EfsSecurityGroup',
                                    allow_all_outbound=False,
                                    vpc=_vpc,
                                    description='Allow EFS access from IPFS Fargate Service'
                                    )

        _efs_sg.add_egress_rule(
            peer=ec2.Peer.ipv4(_vpc.vpc_cidr_block),
            connection=ec2.Port.all_traffic(),
            description='Traffic can only go to internal network'
        )

        _efs_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(_vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(2049),
            description='Incoming NFS connections from the IPFS nodes'
        )

        _alb_ipfs_gateway_target_group = elbv2.ApplicationTargetGroup(
            self, "AlbGatewayTargetGroup",
            target_type=elbv2.TargetType.IP,
            port=8080,
            protocol=elbv2.ApplicationProtocol.HTTP,
            health_check=elbv2.HealthCheck(
                enabled=True,
                path='/ipfs/QmUNLLsPACCz1vLxQVkXqqLX5R1X345qqfHbsf67hvA3Nn',
                healthy_http_codes='200,301,302,303,304,307,308',
            ),
            vpc=_vpc
        )

        _alb_ipfs_gateway_listener = _alb_ipfs_cluster.add_listener(
            'AlbIpfsGatewayListner',
            open=False,
            port=80,
            default_target_groups=[_alb_ipfs_gateway_target_group]
        )

        # Secruity Group for IPFS Fargate Services
        _ipfs_srv_sg = ec2.SecurityGroup(self, 'IpfsServiceSecurityGroup',
                                         vpc=_vpc,
                                         description='Allow access to IPFS nodes'
                                         )

        _ipfs_srv_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(4001),
            description='IPFS swarm port open to the Internet'
        )

        _ipfs_srv_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(_vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(9096),
            description='IPFS Cluster Swarm from internal network only'
        )

        _ipfs_srv_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(_vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5001),
            description='IPFS RPC API from internal network only'
        )

        _ipfs_srv_sg.add_ingress_rule(
            peer=ec2.Peer.security_group_id(
                _alb_ipfs_cluster_sg.security_group_id),
            connection=ec2.Port.tcp(8080),
            description='IPFS Gateway from ALB security group only'
        )

        _ipfs_srv_sg.add_ingress_rule(
            peer=ec2.Peer.security_group_id(
                _alb_ipfs_cluster_sg.security_group_id),
            connection=ec2.Port.tcp(9094),
            description='IPFS Cluster HTTP API from ALB security group only'
        )

        # Private Discovery service for IPFS Nodes
        _private_namespace = cloudmap.PrivateDnsNamespace(
            self, 'FargateServicePrivateDNS',
            vpc=_vpc,
            name=cdk.Aws.STACK_NAME,
            description='Private Discovery service for IPFS Kubo Fargate Srv'
        )

        # Create Cloudfront for IPFS Gateway port 80
        _cf_ipfs_gw = cloudfront.Distribution(
            self, 'CloudfrontIpfsGateway',
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.LoadBalancerV2Origin(
                    _alb_ipfs_cluster,
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            )
        )

        # Create Cloudfront for IPFS Cluster port 9094
        _cf_ipfs_cluster = cloudfront.Distribution(
            self, 'CloudfrontIpfsCluster',
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.LoadBalancerV2Origin(
                    _alb_ipfs_cluster,
                    http_port=9094,
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY
                ),
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
            )
        )

        # Create multi-zone EFS if ONE_ZONE_EFS is FALSE
        if ipfs_cluster_env['ONE_ZONE_EFS'].upper() == 'FALSE':
            _fs = efs.FileSystem(
                self, 'IpfsMultiZoneEfs',
                vpc=_vpc,
                security_group=_efs_sg,
            )

        # Create Fargate Services and related Task/Container
        for i in range(len(_vpc.availability_zones)):
            for j in range(int(ipfs_cluster_env['NODE_PER_AZ'])):
                _ipfs_config_path = '/IpfsKuboEfsAp'+str(i)
                _ipfs_cluster_config_path = '/IpfsClusterEfsAp'+str(i)
                # Create EFS and access point on each subnet
                # Create One-Zone EFS file system
                # https://github.com/aws/aws-cdk/issues/15864
                # if self._parameter_efs_one_zone.value_as_string.upper() == 'TRUE':
                if ipfs_cluster_env['ONE_ZONE_EFS'].upper() == 'TRUE':
                    _fs = efs.FileSystem(
                        self, 'IpfsEfs'+str(i),
                        vpc=_vpc,
                        vpc_subnets=ec2.SubnetSelection(
                            availability_zones=[_vpc.availability_zones[i]],
                            one_per_az=True,
                            subnet_type=ec2.SubnetType.PUBLIC
                        ),
                        security_group=_efs_sg,
                    )
                    _cfn_efs = _fs.node.default_child
                    _cfn_efs.availability_zone_name = _vpc.availability_zones[i]

                # Apply EFS removal policy
                if ipfs_cluster_env['EFS_REMOVE_ON_DELETE'].upper() == 'TRUE':
                    _fs.apply_removal_policy(
                        cdk.RemovalPolicy.DESTROY
                    )
                else:
                    _fs.apply_removal_policy(
                        cdk.RemovalPolicy.RETAIN
                    )

                # ipfs uid = 1000
                # ipfs gid = 100 (users)
                # https://github.com/ipfs/kubo/blob/master/Dockerfile
                # https://github.com/ipfs-cluster/ipfs-cluster/blob/master/Dockerfile
                _ipfs_uid = '1000'
                _ipfs_gid = '100'

                _kubo_efs_ap = _fs.add_access_point(
                    'IpfsKuboAp'+str(i),
                    create_acl=efs.Acl(
                        owner_uid=_ipfs_uid,
                        owner_gid=_ipfs_gid,
                        permissions='755'
                    ),
                    # enforce the POSIX identity
                    posix_user=efs.PosixUser(
                        uid=_ipfs_uid,
                        gid=_ipfs_gid
                    ),
                    path=_ipfs_config_path
                )

                _cluster_efs_ap = _fs.add_access_point(
                    'IpfsClusterAp'+str(i),
                    create_acl=efs.Acl(
                        owner_uid=_ipfs_uid,
                        owner_gid=_ipfs_gid,
                        permissions='755'
                    ),
                    # enforce the POSIX identity
                    posix_user=efs.PosixUser(
                        uid=_ipfs_uid,
                        gid=_ipfs_gid
                    ),
                    path=_ipfs_cluster_config_path
                )

                # Create ECS Fargate Task Definition
                _task = ecs.FargateTaskDefinition(
                    self, 'IpfsFargateTask'+str(i),
                    # compatibility=ecs.Compatibility.FARGATE,
                    cpu=1024,
                    memory_limit_mib=2048,
                    runtime_platform=ecs.RuntimePlatform(
                        operating_system_family=ecs.OperatingSystemFamily.LINUX,
                        cpu_architecture=ecs.CpuArchitecture.X86_64
                    ),
                    volumes=[
                        ecs.Volume(
                            name='IpfsSrvTaskKuboVol'+str(i),
                            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                                file_system_id=_fs.file_system_id,
                                transit_encryption='ENABLED',
                                authorization_config=ecs.AuthorizationConfig(
                                    access_point_id=_kubo_efs_ap.access_point_id,
                                    iam='ENABLED'
                                )
                            )
                        ),
                        ecs.Volume(
                            name='IpfsSrvTaskClusterVol'+str(i),
                            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                                file_system_id=_fs.file_system_id,
                                transit_encryption='ENABLED',
                                authorization_config=ecs.AuthorizationConfig(
                                    access_point_id=_cluster_efs_ap.access_point_id,
                                    iam='ENABLED'
                                )
                            )
                        )
                    ],
                )

                # Add EFS dependence
                _task.node.add_dependency(_fs)

                # Add IPFS Gateway ALB Listener dependence
                _task.node.add_dependency(_alb_ipfs_gateway_listener)

                # Add IPFS Cluster ALB Listener dependence
                _task.node.add_dependency(_alb_ipfs_cluster_listener)

                # Create ECS Fargate Service
                _ipfs_srv = ecs.FargateService(self, 'IpfsSrv'+str(i),
                                               cluster=_ecs_cluster,
                                               task_definition=_task,
                                               assign_public_ip=True,
                                               vpc_subnets=ec2.SubnetSelection(
                    availability_zones=[_vpc.availability_zones[i]],
                    one_per_az=True,
                    subnet_type=ec2.SubnetType.PUBLIC
                ),
                    security_groups=[_ipfs_srv_sg],
                    enable_execute_command=True if ipfs_cluster_env['ECS_EXEC'].upper(
                ) == 'TRUE' else False,
                    cloud_map_options=ecs.CloudMapOptions(
                        cloud_map_namespace=_private_namespace,
                        # Create A records - useful for AWSVPC network mode.
                        dns_record_type=cloudmap.DnsRecordType.A,
                        dns_ttl=Duration.seconds(60),
                        # name='IpfsSrv'+str(i)
                ),
                    max_healthy_percent=100,
                    min_healthy_percent=0
                )

                # Add kubo container
                _kubo_container = _task.add_container(
                    'IpfsKuboNode'+str(i),
                    image=ecs.ContainerImage.from_registry('ipfs/kubo:latest'),
                    port_mappings=[
                        ecs.PortMapping(container_port=4001),
                        ecs.PortMapping(container_port=5001),
                        ecs.PortMapping(container_port=8080),
                    ],
                    health_check=ecs.HealthCheck(
                        command=['/usr/local/bin/ipfs dag stat '
                                 '/ipfs/QmUNLLsPACCz1vLxQVkXqqLX5R1X345qqfHbsf67hvA3Nn'
                                 ' || exit 1 ']
                    ),
                    logging=ecs.LogDriver.aws_logs(
                        stream_prefix='IpfsKuboNode'+str(i)
                    )
                )

                _kubo_container.add_mount_points(
                    ecs.MountPoint(
                        container_path='/data/ipfs',
                        read_only=False,
                        source_volume='IpfsSrvTaskKuboVol'+str(i)
                    )
                )

                # Add ipfs-cluster container
                _container_name = 'IpfsCluster'+str(i)

                # The first ipfs-cluster service will be bootstrap server
                if i == 0:
                    # Other service should wait for first service is ready
                    # since it is the bootstrap server
                    _first_ipfs_service = _ipfs_srv
                    # Retrive first service cloudmap
                    # since the first IPFS node will be the bootstrap server
                    # for other IPFS cluster node
                    _first_cloudmap_service = _ipfs_srv.cloud_map_service
                    _ipfs_cluster_container = _task.add_container(
                        _container_name,
                        image=ecs.ContainerImage.from_registry(
                            'ipfs/ipfs-cluster:latest'
                        ),
                        port_mappings=[
                            ecs.PortMapping(container_port=9096),
                            ecs.PortMapping(container_port=9094),
                        ],
                        health_check=ecs.HealthCheck(
                            command=['/usr/local/bin/ipfs-cluster-ctl --force-http --basic-auth ' +
                                     self._parameter_ipfs_cluster_api_credential.value_as_string + ' || exit 1 ']
                        ),
                        logging=ecs.LogDriver.aws_logs(
                            stream_prefix=_container_name
                        ),
                        environment_files=[
                            ecs.EnvironmentFile.from_asset(
                                './ipfscluster.env',
                                readers=[_task.execution_role]
                            ),
                        ],
                        environment={
                            'CLUSTER_PEERNAME': _container_name,
                            'CLUSTER_ID': _ipfs_cluster_id,
                        },
                        secrets={
                            'CLUSTER_RESTAPI_BASICAUTHCREDENTIALS': _ipfs_cluster_api_credential,
                            'CLUSTER_SECRET': _ipfs_cluster_secret,
                            'CLUSTER_PRIVATEKEY': _ipfs_cluster_private_key,
                        },
                        command=[
                            # '-l' ,'debug',
                            'daemon',
                        ]
                    )
                else:
                    _ipfs_cluster_container = _task.add_container(
                        _container_name,
                        image=ecs.ContainerImage.from_registry(
                            'ipfs/ipfs-cluster:latest'
                        ),
                        port_mappings=[
                            ecs.PortMapping(container_port=9096),
                            ecs.PortMapping(container_port=9094),
                        ],
                        health_check=ecs.HealthCheck(
                            command=['/usr/local/bin/ipfs-cluster-ctl --force-http --basic-auth ' +
                                     self._parameter_ipfs_cluster_api_credential.value_as_string + ' || exit 1 ']
                        ),
                        logging=ecs.LogDriver.aws_logs(
                            stream_prefix=_container_name
                        ),
                        environment_files=[
                            ecs.EnvironmentFile.from_asset(
                                './ipfscluster.env',
                                readers=[_task.execution_role]
                            ),
                        ],
                        environment={
                            'CLUSTER_PEERNAME': _container_name,
                        },
                        command=[
                            # '-l' ,'debug',
                            'daemon',
                            '--bootstrap',
                            '/dns/{_srv_name}.{_srv_ns}/tcp/9096/p2p/{_cluster_id}'.format(
                                _srv_name=_first_cloudmap_service.service_name,
                                _srv_ns=_first_cloudmap_service.namespace.namespace_name,
                                _cluster_id=_ipfs_cluster_id
                            )
                        ],
                        secrets={
                            'CLUSTER_RESTAPI_BASICAUTHCREDENTIALS': _ipfs_cluster_api_credential,
                            'CLUSTER_SECRET': _ipfs_cluster_secret
                        },
                    )
                    # Make sure the bootstrap server is ready
                    _ipfs_srv.node.add_dependency(_first_ipfs_service)

                # Grant EFS access policy
                _fs.grant(
                    _task.execution_role,
                    'elasticfilesystem:*'
                )

                _ipfs_cluster_container.add_mount_points(
                    ecs.MountPoint(
                        container_path='/data/ipfs-cluster',
                        read_only=False,
                        source_volume='IpfsSrvTaskClusterVol'+str(i)
                    )
                )

                _ipfs_cluster_container.add_container_dependencies(
                    ecs.ContainerDependency(
                        container=_kubo_container,
                        condition=ecs.ContainerDependencyCondition.HEALTHY
                    )
                )

                # register kubo to ALB target group
                _alb_ipfs_gateway_target_group.add_target(
                    _ipfs_srv.load_balancer_target(
                        container_name='IpfsKuboNode'+str(i),
                        container_port=8080
                    )
                )

                # register ipfs cluster to ALB target group
                _alb_ipfs_cluster_target_group.add_target(
                    _ipfs_srv.load_balancer_target(
                        container_name='IpfsCluster'+str(i),
                        container_port=9094
                    )
                )

        # Output
        cdk.CfnOutput(
            self, 'IpfsGatewayEndpoint',
            value=_cf_ipfs_gw.domain_name,
            description='DNS of the CloudFront distribution'
            ' for IPFS Gateway. Use this DNS name to'
            ' access IPFS files over HTTPS.'
        )

        cdk.CfnOutput(
            self, 'IpfsClusterEndpoint',
            value=_cf_ipfs_cluster.domain_name,
            description='DNS of the CloudFront distribution'
            ' for IPFS Cluster REST API. Use this DNS'
            ' name to access IPFS Cluster REST API over HTTPS.'
        )

    def _define_parameter(self):

        self._parameter_ipfs_cluster_id = cdk.CfnParameter(
            self, 'ClusterId',
            no_echo=True,
            min_length=52,
            allowed_pattern='^.{52}$'
        )

        self._parameter_ipfs_cluster_secret = cdk.CfnParameter(
            self, 'ClusterSecret',
            no_echo=True,
            min_length=64,
            allowed_pattern='^.{64}$'
        )

        self._parameter_ipfs_cluster_private_key = cdk.CfnParameter(
            self, 'ClusterPrivateKey',
            no_echo=True,
            min_length=92,
            allowed_pattern='^.{92}$'
        )

        self._parameter_ipfs_cluster_api_credential = cdk.CfnParameter(
            self, 'ClusterCredential',
            no_echo=True,
            default='admin:p@ssw0rd'
        )
