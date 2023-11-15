import logging
import os

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from .imagemoderationlambda import ImageModeration
from .imagemoderationvpc import ImageModerationVpc
from .imagemoderationsagemaker import ImageModerationSageMaker
from .envconfig import EnvConfig

logger = logging.getLogger(__name__)


class ChaliceApp(cdk.Stack):

    def __init__(self, scope, id, stage, **kwargs):
        super().__init__(scope, id, **kwargs)

        env_variables = self.node.try_get_context(stage)
        region = os.environ.get("CDK_DEPLOY_REGION",
                                os.environ["CDK_DEFAULT_REGION"])
        account = os.environ.get("CDK_DEPLOY_ACCOUNT",
                                 os.environ["CDK_DEFAULT_ACCOUNT"])

        env_config = EnvConfig.from_dict(
            stage=stage, region=region, account=account, raw_dict=env_variables)

        logger.info('Deploying with env variables: {}'.format(env_config))
        image_moderation_vpc = ImageModerationVpc(
            self,
            'ImageModerationWorkshopVPC',
            env_config)

        image_moderation_sagemaker = ImageModerationSageMaker(self,
                                                              'ImageModerationSageMaker',
                                                              env=env_config,
                                                              vpc=image_moderation_vpc)

        image_moderation_lambda = ImageModeration(
            self,
            'ImageModeration',
            env=env_config,
            vpc=image_moderation_vpc.vpc,
            sagemaker=image_moderation_sagemaker)
