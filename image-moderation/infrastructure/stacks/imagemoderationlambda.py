import os
from uuid import uuid4
from urllib.parse import urlparse

from constructs import Construct

from aws_cdk import (
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_lambda,
    Duration
)

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk.aws_lambda import DockerImageCode, DockerImageFunction

RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, 'runtime')


class ImageModeration(Construct):

    @property
    def rekognition_collection(self):
        return self._rekognition_collection

    def __init__(self, scope: Construct, id: str, env, vpc, sagemaker, **kwargs):
        super().__init__(scope, id)

        self._env = env
        self._vpc = vpc
        self._sagemaker = sagemaker

        self.create_chalice_app()

    def create_chalice_app(self):
        self._principal = iam.ServicePrincipal("lambda.amazonaws.com")
        default_role = self._create_role(self._sagemaker.endpoint_ref)

        self._docker_lambda = aws_lambda.DockerImageFunction(
            self,
            'WorkshopDockerLambda',
            code=DockerImageCode.from_image_asset('../runtime'),
            # architecture=aws_lambda.Architecture.ARM_64,
            timeout=Duration.seconds(60 * 15),  # Default is only 3 seconds
            memory_size=2048,  # If your docker code is pretty complex
            environment={
                'MODERATION_REKOGNITION_COLLECTION_ID': self._env.moderation_rekognition_collection_id,
                'MODERATION_CUSTOMER_FACIAL_THRESHOLD': str(self._env.moderation_customer_facial_threshold),
                'MODERATION_ANIMATION_EXTRACTION_SMALL_DEFAULT_MAX_THRESHOLD': str(self._env.moderation_animation_extraction_small_default_max_threshold),
                'MODERATION_ANIMATION_EXTRACTION_LARGE_DEFAULT_THRESHOLD_SIZE': str(self._env.moderation_animation_extraction_large_default_threshold_size),
                'MODERATION_ANIMATION_EXTRACTION_SIZE_THRESHOLD': str(self._env.moderation_animation_extraction_size_threshold),
                'MODERATION_IMAGE_COMPRESS_QUALITY_STEP': str(self._env.moderation_image_compress_quality_step),
                'MODERATION_IMAGE_COMPRESSION_SIZE_THRESHOLD': str(self._env.moderation_image_compression_size_threshold),
                'MODERATION_CELEBRITY_FACIAL_THRESHOLD': str(self._env.moderation_celebrity_facial_threshold),
                'MODERATION_DETECT_LABEL_INCLUSION_FILTER': self._env.moderation_detect_label_inclusion_filter,
                'MODERATION_DETECT_MODERATION_LABEL_FILTER_ENABLED': str(self._env.moderation_detect_moderation_label_filter_enabled),
                'MODERATION_DETECT_MODERATION_LABEL_INCLUSION_FILTER': self._env.moderation_detect_moderation_label_inclusion_filter,
                'MODERATION_BACKEND_SERVICES': self._env.moderation_backend_services,
                'MODERATION_IMAGE_BLACKLIST_WHITELIST_ENABLED': str(self._env.moderation_image_blacklist_whitelist_enabled),
                'SAGEMAKER_ENDPOINT_NAME': self._sagemaker.endpoint_name
            },
            role=default_role,
            vpc=self._vpc
        )

        api_gateway = self._create_api_gateway(self._docker_lambda)
        self._add_permission_for_api_gateway(principal=self._principal,
                                             api_gateway=api_gateway)

        cdk.CfnOutput(self, "LambdaRoleName", value=default_role.role_name)

    def _create_role(self, sagemaker_endpoint_ref):
        default_role = iam.Role(self, "DefaultWorkshopRole",
                                assumed_by=self._principal)

        default_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    f'arn:{self._env.deploy_partition}:logs:{self._env.region}:{self._env.account}:*'],
                effect=iam.Effect.ALLOW,
            )
        )
        default_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DetachNetworkInterface",
                    "ec2:DeleteNetworkInterface"
                ],
                resources=['*'],
                effect=iam.Effect.ALLOW,
            )
        )

        # grant rekognition permissions
        default_role.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rekognition:DetectLabels",
                    "rekognition:DetectModerationLabels",
                    "rekognition:SearchFacesByImage",
                    "rekognition:RecognizeCelebrities",
                ],
                resources=['*']
            )
        )

        # grant sagemaker role
        default_role.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sagemaker:InvokeEndpoint"],
                resources=[sagemaker_endpoint_ref],
            )

        )

        return default_role

    def _add_permission_for_api_gateway(self,
                                        principal,
                                        api_gateway):
        """Authorize API gateway to invoke docker lambda function is needed.

        This method will first check if API gateway has permission to call
        the lambda function, and only if necessary will it invoke

        """
        self._docker_lambda.add_permission(id='APIHandlerInvokePermission',
                                           action='lambda:InvokeFunction',
                                           principal=principal,
                                           source_arn=api_gateway.arn_for_execute_api())

    def _create_api_gateway(self, lambda_docker):

        api = apigateway.LambdaRestApi(self,
                                       "image-moderation-workshop",
                                       handler=lambda_docker,
                                       # endpoint_types=[apigateway.EndpointType.EDGE]
                                       proxy=False,
                                       deploy_options={
                                           'logging_level': apigateway.MethodLoggingLevel.INFO,
                                           'data_trace_enabled': True
                                       })

        root_resource = api.root.add_resource("Moderation")
        self._add_detection_resources_to_api_gateway(
            root_resource.add_resource("DetectImageLabels"))

        return api

    # add api_key_required
    def _add_detection_resources_to_api_gateway(self, parent_resource: apigateway.Resource):
        parent_resource.add_method("POST", authorization_type=apigateway.AuthorizationType.IAM)
        parent_resource.add_cors_preflight(allow_origins=apigateway.Cors.ALL_ORIGINS, allow_methods=['POST'])
