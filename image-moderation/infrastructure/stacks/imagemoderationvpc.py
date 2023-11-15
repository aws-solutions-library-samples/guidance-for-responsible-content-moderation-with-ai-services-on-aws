from constructs import Construct

from aws_cdk import aws_ec2 as ec2


class ImageModerationVpc(Construct):
    def __init__(self, scope: Construct, id: str, env, **kwargs):
        super().__init__(scope, id)

        self._env = env
        self._scope = scope

        self._vpc = ec2.Vpc(
            self,
            "ImageModerationWorkshopVPC",
            max_azs=4,
            ip_addresses= ec2.IpAddresses.cidr(env.moderation_vpc_cidr),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=24,
                ),
            ],
            nat_gateways=1,
        )

        # add flow log
        self._vpc.add_flow_log("FlowLogWorkshopVPC")

        self._sg = ec2.SecurityGroup(
            self,
            "vpce-sg",
            vpc=self._vpc,
            allow_all_outbound=True,
            description="allow tls for vpc endpoint",
        )

    @property
    def security_groups(self):
        return [self._sg]

    @property
    def subnet_selection(self):
        return self._vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets

    @property
    def vpc(self):
        return self._vpc

    @property
    def vpc_endpoint(self):
        return self._vpc.endpoint_id
