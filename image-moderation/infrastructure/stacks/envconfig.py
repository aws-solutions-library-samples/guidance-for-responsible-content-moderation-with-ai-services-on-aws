import json
from collections import defaultdict


class EnvConfig:
    def __init__(self,
                 stage='dev',
                 region='us-east-1',
                 account='',
                 pytorch_version='1.13.1',
                 py_version='py39',
                 moderation_vpc_cidr='10.128.0.0/16',
                 moderation_customer_facial_threshold=85,
                 moderation_celebrity_facial_threshold=95,
                 moderation_animation_extraction_small_default_max_threshold=8,
                 moderation_animation_extraction_large_default_threshold_size=25,
                 moderation_animation_extraction_size_threshold=5242880,
                 moderation_image_compression_size_threshold=524288,
                 moderation_image_compress_quality_step=8,
                 moderation_detect_label_inclusion_filter='',
                 moderation_detect_moderation_label_filter_enabled=False,
                 moderation_detect_moderation_label_inclusion_filter='',
                 moderation_rekognition_collection_id='collection_id',
                 moderation_backend_services='DetectLabels,DetectModerationLabels,FaceSearch,CelebritySearch,DetectByCustomModels',
                 moderation_image_blacklist_whitelist_enabled=True,
                 moderation_image_blacklist_whitelist_read_capacity=100,
                 moderation_image_blacklist_whitelist_write_capacity=20,
                 sagemaker_endpoint_instance_type='ml.g4dn.2xlarge',
                 sagemaker_endpoint_instance_count=6,
                 sagemaker_endpoint_workers=7,
                 sagemaker_min_capacity=6,
                 sagemaker_max_capacity=8,
                 enable_sagemaker_notebook=True,
                 sagemaker_logging_level=20,
                 enable_sagemaker_autoscaling=False,
                 sagemaker_image_uri='',
                 sagemaker_inference_model_name='inference.tar.gz'):
        self.stage = stage
        self.region = region
        self.account = account
        self.pytorch_version = pytorch_version
        self.py_version = py_version
        self.moderation_vpc_cidr = moderation_vpc_cidr
        self.moderation_customer_facial_threshold = moderation_customer_facial_threshold
        self.moderation_celebrity_facial_threshold = moderation_celebrity_facial_threshold
        self.moderation_animation_extraction_small_default_max_threshold = moderation_animation_extraction_small_default_max_threshold
        self.moderation_animation_extraction_large_default_threshold_size = moderation_animation_extraction_large_default_threshold_size
        self.moderation_animation_extraction_size_threshold = moderation_animation_extraction_size_threshold
        self.moderation_image_compression_size_threshold = moderation_image_compression_size_threshold
        self.moderation_image_compress_quality_step = moderation_image_compress_quality_step
        self.moderation_detect_label_inclusion_filter = moderation_detect_label_inclusion_filter
        self.moderation_detect_moderation_label_filter_enabled = moderation_detect_moderation_label_filter_enabled
        self.moderation_detect_moderation_label_inclusion_filter = moderation_detect_moderation_label_inclusion_filter
        self.moderation_rekognition_collection_id = moderation_rekognition_collection_id
        self.moderation_backend_services = moderation_backend_services
        self.moderation_image_blacklist_whitelist_enabled = moderation_image_blacklist_whitelist_enabled
        self.moderation_image_blacklist_whitelist_read_capacity = moderation_image_blacklist_whitelist_read_capacity
        self.moderation_image_blacklist_whitelist_write_capacity = moderation_image_blacklist_whitelist_write_capacity
        self.sagemaker_endpoint_instance_type = sagemaker_endpoint_instance_type
        self.sagemaker_endpoint_instance_count = sagemaker_endpoint_instance_count
        self.sagemaker_endpoint_workers = sagemaker_endpoint_workers
        self.sagemaker_min_capacity = sagemaker_min_capacity
        self.sagemaker_max_capacity = sagemaker_max_capacity
        self.enable_sagemaker_notebook = enable_sagemaker_notebook
        self.sagemaker_logging_level = sagemaker_logging_level
        self.enable_sagemaker_autoscaling = enable_sagemaker_autoscaling
        self.sagemaker_image_uri = sagemaker_image_uri
        self.sagemaker_inference_model_name = sagemaker_inference_model_name

        # get partition
        self.deploy_partition = "aws"
        if region.startswith("cn"):
            self.deploy_partition = "aws-cn"

    def __iter__(self):
        yield from {
            "stage": self.stage,
            "region": self.region,
            "account": self.account,
            "pytorch_version": self.pytorch_version,
            "py_version": self.py_version,
            "moderation_vpc_cidr": self.moderation_vpc_cidr,
            "moderation_customer_facial_threshold": self.moderation_customer_facial_threshold,
            "moderation_celebrity_facial_threshold": self.moderation_celebrity_facial_threshold,
            "moderation_animation_extraction_small_default_max_threshold": self.moderation_animation_extraction_small_default_max_threshold,
            "moderation_animation_extraction_large_default_threshold_size": self.moderation_animation_extraction_large_default_threshold_size,
            "moderation_animation_extraction_size_threshold": self.moderation_animation_extraction_size_threshold,
            "moderation_image_compress_quality_step": self.moderation_image_compress_quality_step,
            "moderation_image_compression_size_threshold": self.moderation_image_compression_size_threshold,
            "moderation_detect_label_inclusion_filter": self.moderation_detect_label_inclusion_filter,
            "moderation_detect_moderation_label_filter_enabled": self.moderation_detect_moderation_label_filter_enabled,
            "moderation_detect_moderation_label_inclusion_filter": self.moderation_detect_moderation_label_inclusion_filter,
            "moderation_rekognition_collection_id": self.moderation_rekognition_collection_id,
            "deploy_partition": self.deploy_partition,
            "sagemaker_endpoint_instance_type": self.sagemaker_endpoint_instance_type,
            "sagemaker_endpoint_instance_count": self.sagemaker_endpoint_instance_count,
            "sagemaker_endpoint_workers": self.sagemaker_endpoint_workers,
            "sagemaker_min_capacity": self.sagemaker_min_capacity,
            "sagemaker_max_capacity": self.sagemaker_max_capacity,
            "enable_sagemaker_notebook": self.enable_sagemaker_notebook,
            "sagemaker_logging_level": self.sagemaker_logging_level,
            "enable_sagemaker_autoscaling": self.enable_sagemaker_autoscaling,
            "sagemaker_image_uri": self.sagemaker_image_uri,
            "sagemaker_inference_model_name": self.sagemaker_inference_model_name
        }.items()

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def to_json(self):
        return self.__str__()

    def is_dev(self) -> bool:
        return self.stage == 'dev'

    @staticmethod
    def from_dict(stage='dev', region='us-east-1', account='', raw_dict=None):
        json_dct = defaultdict(str, raw_dict)
        return EnvConfig(
            stage,
            region,
            account,
            json_dct['pytorch_version'],
            json_dct['py_version'],
            json_dct['moderation_vpc_cidr'],
            json_dct['moderation_customer_facial_threshold'],
            json_dct['moderation_celebrity_facial_threshold'],
            json_dct['moderation_animation_extraction_small_default_max_threshold'],
            json_dct['moderation_animation_extraction_large_default_threshold_size'],
            json_dct['moderation_animation_extraction_size_threshold'],
            json_dct['moderation_image_compression_size_threshold'],
            json_dct['moderation_image_compress_quality_step'],
            json_dct['moderation_detect_label_inclusion_filter'],
            json_dct['moderation_detect_moderation_label_filter_enabled'],
            json_dct['moderation_detect_moderation_label_inclusion_filter'],
            json_dct['moderation_rekognition_collection_id'],
            json_dct['moderation_backend_services'],
            json_dct['moderation_image_blacklist_whitelist_enabled'],
            json_dct['moderation_image_blacklist_whitelist_read_capacity'],
            json_dct['moderation_image_blacklist_whitelist_write_capacity'],
            json_dct['sagemaker_endpoint_instance_type'],
            json_dct['sagemaker_endpoint_instance_count'],
            json_dct['sagemaker_endpoint_workers'],
            json_dct['sagemaker_min_capacity'],
            json_dct['sagemaker_max_capacity'],
            json_dct['enable_sagemaker_notebook'],
            json_dct['sagemaker_logging_level'],
            json_dct['enable_sagemaker_autoscaling'],
            json_dct['sagemaker_image_uri'],
            json_dct['sagemaker_inference_model_name'])
