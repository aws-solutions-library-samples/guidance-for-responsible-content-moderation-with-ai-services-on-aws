from aws_cdk import (
    aws_iam as iam,
    aws_kms as kms,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudwatch as cloudwatch,
    aws_sagemaker as sagemaker,
    aws_applicationautoscaling as asg,
)
from constructs import Construct

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk


region_dict = {
    "af-south-1": "626614931356",
    "ap-east-1": "871362719292",
    "ap-northeast-1": "763104351884",
    "ap-northeast-2": "763104351884",
    "ap-northeast-3": "364406365360",
    "ap-south-1": "763104351884",
    "ap-southeast-1": "763104351884",
    "ap-southeast-2": "763104351884",
    "ca-central-1": "763104351884",
    "cn-north-1": "727897471807",
    "cn-northwest-1": "727897471807",
    "eu-central-1": "763104351884",
    "eu-north-1": "763104351884",
    "eu-south-1": "692866216735",
    "eu-west-1": "763104351884",
    "eu-west-2": "763104351884",
    "eu-west-3": "763104351884",
    "me-south-1": "217643126080",
    "sa-east-1": "763104351884",
    "us-east-1": "763104351884",
    "us-east-2": "763104351884",
    "us-gov-west-1": "442386744353",
    "us-iso-east-1": "886529160074",
    "us-west-1": "763104351884",
    "us-west-2": "763104351884",
}


class ImageModerationSageMaker(Construct):
    @property
    def bucket_name(self):
        return self._bucket_name

    @property
    def endpoint_name(self):
        return self._endpoint_name

    @property
    def endpoint_ref(self):
        return self._endpoint_ref

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id)

        self._env = kwargs['env']
        self._deploy_partition = self._env.deploy_partition

        # self._data_bucket = self._create_data_bucket()
        self._sagemaker_role = self._create_role()

        # if self._env.enable_sagemaker_notebook:
        #     self._create_sagemaker_notebook(self._notebook_role.role_arn)
        model_file = f's3://sagemaker-{self._env.region}-{self._env.account}/output/inference-pytorch.tar.gz'

        endpoint = self._create_endpoint(model_file)

        # self._bucket_name = self._data_bucket.bucket_name
        self._endpoint_name = endpoint.attr_endpoint_name
        self._endpoint_ref = endpoint.ref

        cdk.CfnOutput(self, "SageMakerCustomModelWorkshopEndPoint", value=self._endpoint_name)

    def _create_endpoint(self, model_file):
        prefix = "CustomLabelWorkshop"
        instance_type = self._env.sagemaker_endpoint_instance_type
        instance_count = self._env.sagemaker_endpoint_instance_count

        image_uri = self._get_sagemaker_image_uri()
        print(f'Inference image uri: {image_uri}')
        # ===========================
        # ===== SAGEMAKER MODEL =====
        # ===========================
        model = sagemaker.CfnModel(
            self,
            f"{prefix}Model",
            execution_role_arn=self._sagemaker_role.role_arn,
            # the properties below are optional
            enable_network_isolation=False,
            containers=[
                sagemaker.CfnModel.ContainerDefinitionProperty(
                    container_hostname="container1",
                    # image=image_uri,
                    image=image_uri,
                    mode="SingleModel",
                    model_data_url=model_file,
                    environment={
                        "SAGEMAKER_CONTAINER_LOG_LEVEL": self._env.sagemaker_logging_level,
                        "SAGEMAKER_PROGRAM": "inference.py",
                        "SAGEMAKER_REGION": cdk.Aws.REGION,
                        "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code",
                        "SAGEMAKER_TS_BATCH_SIZE": '4',
                        "SAGEMAKER_TS_MAX_BATCH_DELAY": '100',
                        "SAGEMAKER_TS_MAX_WORKERS": self._env.sagemaker_endpoint_workers,
                        "SAGEMAKER_TS_MIN_WORKERS": self._env.sagemaker_endpoint_workers
                    },
                )
            ],
        )
        # model.node.add_dependency(self.model_deployment)

        # =====================================
        # ===== SAGEMAKER ENDPOINT CONFIG =====
        # =====================================
        variant_name = "AllTraffic"
        endpoint_config = sagemaker.CfnEndpointConfig(
            self,
            f"{prefix}EndpointConfig",
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    initial_instance_count=instance_count,
                    initial_variant_weight=1.0,
                    instance_type=instance_type,
                    model_name=model.attr_model_name,
                    variant_name=variant_name,
                )
            ],
        )

        endpoint_config.add_depends_on(model)
        # ==============================
        # ===== SAGEMAKER ENDPOINT =====
        # ==============================

        endpoint = sagemaker.CfnEndpoint(
            self,
            f"{prefix}Endpoint",
            endpoint_config_name=endpoint_config.attr_endpoint_config_name,
        )
        cdk.CfnOutput(
            self, "Sagemaker_Model_Endpoint", value=endpoint.attr_endpoint_name
        )

        if self._env.enable_sagemaker_autoscaling:
            # add the autoscaling policy
            target = asg.ScalableTarget(
                self,
                "ScalableTarget",
                service_namespace=asg.ServiceNamespace.SAGEMAKER,
                max_capacity=self._env.sagemaker_max_capacity,
                min_capacity=self._env.sagemaker_min_capacity,
                resource_id=f"endpoint/{endpoint.attr_endpoint_name}/variant/{variant_name}",
                scalable_dimension="sagemaker:variant:DesiredInstanceCount",
                role=self._sagemaker_role
            )
            target.node.add_dependency(endpoint)

            target.scale_to_track_metric(
                "GPU35Tracking",
                target_value=35,
                custom_metric=cloudwatch.Metric(
                    metric_name="GPUUtilization",
                    namespace="/aws/sagemaker/Endpoints",
                    period=cdk.Duration.minutes(1),
                    dimensions_map={
                        "EndpointName": endpoint.attr_endpoint_name,
                        "VariantName": variant_name
                    },
                    statistic="Average",
                ),
                scale_in_cooldown=cdk.Duration.seconds(600),
                scale_out_cooldown=cdk.Duration.seconds(300),
            )

        return endpoint

    # def _create_data_bucket(self):
    #     data_bucket = s3.Bucket(
    #         self,
    #         "data",
    #         removal_policy=cdk.RemovalPolicy.RETAIN,
    #         encryption=s3.BucketEncryption.S3_MANAGED,
    #         block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
    #         server_access_logs_prefix='access_log_'
    #     )
    #
    #     data_bucket.add_to_resource_policy(
    #         iam.PolicyStatement(
    #             sid="AllowSSLRequestsOnly",
    #             effect=iam.Effect.DENY,
    #             actions=["s3:*"],
    #             conditions={"Bool": {"aws:SecureTransport": "false"}},
    #             principals=[iam.AnyPrincipal()],
    #             resources=[
    #                 data_bucket.arn_for_objects("*"),
    #                 data_bucket.bucket_arn,
    #             ],
    #         )
    #     )
    #
    #     cdk.CfnOutput(self, "DataBucketName", value=data_bucket.bucket_name)
    #     return data_bucket

    def _create_role(self):
        # IAM Roles
        name = "SagemakerWorkshop"
        notebook_role = iam.Role(
            self,
            f"{name}Role",
            description="Sagemaker image detection workshop role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy(
                    self,
                    f"{name}Policy",
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:GetBucketAcl",
                                "s3:PutObjectAcl",
                                "s3:AbortMultipartUpload",
                            ],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetObject"],
                            resources=["*"],
                            conditions={
                                "StringEqualsIgnoreCase": {
                                    "s3:ExistingObjectTag/SageMaker": "true"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["iam:PassRole"],
                            resources=["*"],
                            conditions={
                                "StringEquals": {
                                    "iam:PassedToService": "sagemaker.amazonaws.com"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetBucketAcl", "s3:PutObjectAcl"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*sagemaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*SageMaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*Sagemaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*LabelingFunction*",
                            ],
                        ),
                        iam.PolicyStatement(
                            actions=["s3:ListBucket"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            actions=["s3:CreateBucket"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "sagemaker:DescribeEndpointConfig",
                                "sagemaker:DescribeModel",
                                "sagemaker:InvokeEndpoint",
                                "sagemaker:ListTags",
                                "sagemaker:DescribeEndpoint",
                                "sagemaker:CreateModel",
                                "sagemaker:CreateEndpointConfig",
                                "sagemaker:CreateEndpoint",
                                "sagemaker:DeleteModel",
                                "sagemaker:DeleteEndpointConfig",
                                "sagemaker:DeleteEndpoint",
                                "sagemaker:CreateTrainingJob",
                                "sagemaker:DescribeTrainingJob",
                                "sagemaker:UpdateEndpoint",
                                "sagemaker:UpdateEndpointWeightsAndCapacities",
                                "autoscaling:*",
                                "ecr:GetAuthorizationToken",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:SetRepositoryPolicy",
                                "ecr:CompleteLayerUpload",
                                "ecr:BatchDeleteImage",
                                "ecr:UploadLayerPart",
                                "ecr:DeleteRepositoryPolicy",
                                "ecr:InitiateLayerUpload",
                                "ecr:DeleteRepository",
                                "ecr:PutImage",
                                "ecr:CreateRepository",
                                "ec2:CreateVpcEndpoint",
                                "ec2:DescribeRouteTables",
                                "cloudwatch:PutMetricData",
                                "cloudwatch:GetMetricData",
                                "cloudwatch:GetMetricStatistics",
                                "cloudwatch:ListMetrics",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:GetLogEvents",
                                "logs:CreateLogGroup",
                                "logs:DescribeLogStreams",
                                "iam:ListRoles",
                                "iam:GetRole",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["kms:Decrypt",
                                     "kms:Encrypt", "kms:CreateGrant"],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["iam:CreateServiceLinkedRole"],
                            resources=[
                                "arn:aws:iam::*:role/aws-service-role/sagemaker.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_SageMakerEndpoint"
                            ],
                            conditions={
                                "StringLike": {
                                    "iam:AWSServiceName": "sagemaker.application-autoscaling.amazonaws.com",
                                }
                            },
                        ),
                    ],
                )
            ],
        )

        cdk.CfnOutput(self, "SagemakerWorkshopRoleName", value=notebook_role.role_name)

        return notebook_role

    def _get_sagemaker_image_uri(self):
        if self._env.sagemaker_image_uri != '':
            return self._env.sagemaker_image_uri
        else:
            return self._get_sagemaker_default_image_uri()

    def _is_gpu_instance(self):
        return True if self._env.sagemaker_endpoint_instance_type.split(".")[1][0].lower() in ["p", "g"] else False

    def _get_sagemaker_default_image_uri(self):
        region = self._env.region
        use_gpu = self._is_gpu_instance()
        pytorch_version = self._env.pytorch_version
        py_version = self._env.py_version

        repository = (
            f"{region_dict[region]}.dkr.ecr.{region}.amazonaws.com/pytorch-inference"
        )
        tag = f"{pytorch_version}-{'gpu' if use_gpu == True else 'cpu'}-{py_version}"
        return f"{repository}:{tag}"
