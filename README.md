
# Guidance for Responsible Content Moderation with AI Services on AWS

## Overview
This application is to moderate images with aws services. It could identify inappropriate contents like png/jpeg/gif images with labels.

After cloning this repository,

* You can train a small model for customized moderation scenarios
* Then you need to deploy the image solution via CDK
* You can test with images

## Cost

You are responsible for the cost of the AWS services used while running this Guidance. 

## Prerequisites
### Skills
To complete the workshop, we recommend that you have some basic experience with the following:
- Python3: You must be able to read and understand Python code 
- Docker: With Docker, you can manage your infrastructure in the same ways you manage your applications. 
- ML basic experience, for example be familiar with a common ML development cycle, data processing approaches, and be aware about basic ML algorithms and ML model building process. If you'd like to complete the assignments, you must be familiar with Python programming, Jupyter notebooks and ML fundamentals.
- [AWS SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html): Amazon SageMaker is a fully managed machine learning (ML) service. With SageMaker, data scientists and developers can quickly and confidently build, train, and deploy ML models into a production-ready hosted environment. 

### Operating System
You need to
* prepare an ec2 instance with a Linux(Amazon Linux is recommended) x86_64 architecture(t3.xlarge is recommended) for the deployment
  * Install nodejs: If you haven't installed a stable LTS version for nodejs which is required to install CDK, please refer to [Installing and Updating](https://github.com/nvm-sh/nvm#installing-and-updating) to manage and install nodejs. You can find the stable LTS versions via [Nodejs Releases](https://nodejs.org/en/about/previous-releases), and then install or change it by
    ```shell
    nvm install <Stable LTS Version> ## install a LTS Version
    nvm use <Stable LTS Version>  ## activate this Version in use
    ```
  * install cdk in this deployment machine and get your account bootstrapped, please refer to [Install the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)
  * install docker in this deployment machine de and start the docker: 
    ```shell
    $ sudo yum install docker
    $ sudo usermod -aG docker ${USER} 
    $ sudo systemctl start docker
    ```
* prepare a SageMaker Notebook instance(ml.t3.xlarge) to build your own custom model. Amazon SageMaker is a fully managed machine learning (ML) service. We use [SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html) to run an Jupyter Notebook instance to build your own custom model for specified content moderation dectection.
* Download the demo code on your EC2 instance you just created for deployment, 
  ```shell
    $ git clone https://github.com/aws-solutions-library-samples/guidance-for-ai-powered-ugc-content-moderation-on-aws.git
  ```

### Third-party tools
N/A

### AWS account requirements

This deployment requires the following available in your AWS account

**Required resources:**
- AWS S3 bucket
- AWS VPC
- AWS IAM role with specific permissions
- AWS Rekognition
- AWS SageMaker

Make sure your account can utility the above resources.

## Train a custom model
You can create sagemaker notebook as prerequisites required and follow the steps in `custom-model-train/ContentModerationWorkshop.ipynb` to train a model

## Deploy image solution
Before you deploy an application, be sure you have right aws credentials configured.
Now you need to install deployment dependencies.
```shell
  $ cd image-moderation/infrastructure
  $ python3 -m venv .venv
  $ source .venv/bin/activate
  $ pip install -r requirements.txt
```

With different profile you can deploy to different environment with different configuration.
For this example, you can try with 'workshop' profile by the following command::
```
  $ cdk deploy -c config=workshop
```

When it's done, the command prompt reappears. You can go to the AWS CloudFormation console and see that it now lists image-moderation-workshop.

## Test

After deployment, you can get an url of your content moderation url in output cdk.
image-moderation-workshop.ImageModerationimagemoderationworkshopEndpoint** = https://**.execute-api.**.amazonaws.com/prod/
As this api is protected, you must specify a user who has the permission to invoke this api to test with AWS IAM V4 auth in your client. Alternatively, you can test via APIGateway Console, please refer to [API Gateway console test](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-test-method.html). 
You can post data as the following,
    {
      "Image": {
        "Url": "image url, you can put tulip image or some moderation image"
      },
      "MaxLabels": 10,
      "MinConfidence": 50,
      "ReturnSource": [
        "DetectModerationLabels",
        "DetectLabels",
        "CelebritySearch",
        "DetectByCustomModels"
      ]
    }

> **_NOTE:_**  
> For `ReturnSource`, please refer to the following:
> * DetectModerationLabels: This invokes [DetectModerationLabels](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_DetectModerationLabels.html) of AWS Rekognition API
> * DetectLabels: This invokes [DetectLabels](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_DetectLabels.html) of AWS Rekognition API
> * CelebritySearch: This invokes [RecognizeCelebrities](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_RecognizeCelebrities.html) of AWS Rekognition API
> * DetectByCustomModels: This invokes API from SageMaker which runs your custom built model.

### Service limits  (if applicable)

The solution can handle media format in one of the followings:
* PNG
* GIF
* JPG/JPEG
* WEBP
* MP4

### Supported Regions

Currently it only support regions which have AWS Rekognition and SageMaker available.

## Cleanup
### Terminate The Solution
Please kick `cdk destroy` to clean up the whole environment in this path `image-moderation/infrastructure`.

### Terminate Deployment EC2
Now you can follow this link [Terminate your instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html) to destroy your deployment EC2 if you've setup for this solution only.

## FAQ, known issues, additional considerations, and limitations
N/A

## Revisions
N/A

## Notices
During the launch of this reference architecture,
you will install software (and dependencies) on the Amazon EC2 instances launched
in your account via stack creation.
The software packages and/or sources you will install
will be from the Amazon Linux distribution and AWS Services, as well as from third party sites.
Here is the list of third party software, the source link,
and the license link for each software.
Please review and decide your comfort with installing these before continuing.

BSD License: https://opensource.org/licenses/bsd-license.php

Historical Permission Notice and Disclaimer (HPND): https://opensource.org/licenses/HPND

MIT License: https://github.com/tsenart/vegeta/blob/master/LICENSE

Apache Software License 2.0: https://www.apache.org/licenses/LICENSE-2.0

Mozilla Public License 2.0 (MPL 2.0): https://www.mozilla.org/en-US/MPL/2.0/

ISC License: https://opensource.org/licenses/ISC

GNU LGPL 2.1: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html

