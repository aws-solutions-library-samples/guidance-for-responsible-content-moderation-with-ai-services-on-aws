===================================
Media Content Moderation Application
===================================

Overview
========
This application is to moderate images with aws services. It could identify inappropriate contents like png/jpeg/gif images or videos with labels.

After cloning this repository,

* You can train a small model for customized moderation scenarios
* Then you can deploy the image content moderation solution via CDK
* Then you can deploy video solution
* You can test with image or video

Train a custom model
--------------------
You can create sagemaker notebook and follow the steps in `custom-model-train/ContentModerationWorkshop.ipynb` to train a model

Deploy image content moderation
-------------------------------
Before you can deploy an application, be sure you have
aws credentials configured.

You need to
* prepare an ec2 instance with x86_64 architecture for the deployment
* install cdk in this deployment machine and get your account bootstrapped, please refer to `Install the AWS CDK <https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install>`_
* install docker in this deployment machine de and start the docker:: console
    
    :linenos:

  $ sudo yum install docker
  $ sudo systemctl start docker

Then you need to install dependencies::

  $ cd image-moderation/infrastructure
  $ python3 -m venv .venv
  $ . venv/bin/activate
  $ pip install -r requirements.txt

With different profile you can deploy to different environment with different configuration.
For this example, you can try with 'dev' profile by the following command::

  $ cdk deploy -c config=dev

Deploy video content moderation
-------------------------------

TODO

Test
----
After deployment, you can get a url of your content moderation url in output cdk.
image-moderation-workshop.ImageModerationimagemoderationworkshopEndpoint** = https://**.execute-api.**.amazonaws.com/prod/
As this api is protected, you must specify a user who has the permission to invoke this api to test with AWS IAM V4 auth.
You can post data as the following::

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
        "DetectModerationLabels",
        "DetectByCustomModels"
      ]
    }

notes::

  "DetectModerationLabels",
  "DetectLabels",
  "CelebritySearch",
  "DetectModerationLabels",
  "DetectByCustomModels"
--------------

# Guidance Title (required)

The Guidance title should be consistent with the title established first in Alchemy.

**Example:** *Guidance for Product Substitutions on AWS*

This title correlates exactly to the Guidance it’s linked to, including its corresponding sample code repository.


## Table of Content (required)

List the top-level sections of the README template, along with a hyperlink to the specific section.

### Required

1. [Overview](#overview-required)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites-required)
    - [Operating System](#operating-system-required)
3. [Deployment Steps](#deployment-steps-required)
4. [Deployment Validation](#deployment-validation-required)
5. [Running the Guidance](#running-the-guidance-required)
6. [Next Steps](#next-steps-required)
7. [Cleanup](#cleanup-required)

***Optional***

8. [FAQ, known issues, additional considerations, and limitations](#faq-known-issues-additional-considerations-and-limitations-optional)
9. [Revisions](#revisions-optional)
10. [Notices](#notices-optional)
11. [Authors](#authors-optional)

## Overview (required)

1. Provide a brief overview explaining the what, why, or how of your Guidance. You can answer any one of the following to help you write this:

    - **Why did you build this Guidance?**
    - **What problem does this Guidance solve?**

2. Include the architecture diagram image, as well as the steps explaining the high-level overview and flow of the architecture.
    - To add a screenshot, create an ‘assets/images’ folder in your repository and upload your screenshot to it. Then, using the relative file path, add it to your README.

### Cost

This section is for a high-level cost estimate. Think of a likely straightforward scenario with reasonable assumptions based on the problem the Guidance is trying to solve. If applicable, provide an in-depth cost breakdown table in this section.

Start this section with the following boilerplate text:

_You are responsible for the cost of the AWS services used while running this Guidance. As of <month> <year>, the cost for running this Guidance with the default settings in the <Default AWS Region (Most likely will be US East (N. Virginia)) > is approximately $<n.nn> per month for processing ( <nnnnn> records )._

Replace this amount with the approximate cost for running your Guidance in the default Region. This estimate should be per month and for processing/serving resonable number of requests/entities.


## Prerequisites (required)

### Operating System (required)

- Talk about the base Operating System (OS) and environment that can be used to run or deploy this Guidance, such as *Mac, Linux, or Windows*. Include all installable packages or modules required for the deployment.
- By default, assume Amazon Linux 2/Amazon Linux 2023 AMI as the base environment. All packages that are not available by default in AMI must be listed out.  Include the specific version number of the package or module.

**Example:**
“These deployment instructions are optimized to best work on **<Amazon Linux 2 AMI>**.  Deployment in another OS may require additional steps.”

- Include install commands for packages, if applicable.


### Third-party tools (If applicable)

*List any installable third-party tools required for deployment.*


### AWS account requirements (If applicable)

*List out pre-requisites required on the AWS account if applicable, this includes enabling AWS regions, requiring ACM certificate.*

**Example:** “This deployment requires you have public ACM certificate available in your AWS account”

**Example resources:**
- ACM certificate
- DNS record
- S3 bucket
- VPC
- IAM role with specific permissions
- Enabling a Region or service etc.


### aws cdk bootstrap (if sample code has aws-cdk)

<If using aws-cdk, include steps for account bootstrap for new cdk users.>

**Example blurb:** “This Guidance uses aws-cdk. If you are using aws-cdk for first time, please perform the below bootstrapping....”

### Service limits  (if applicable)

<Talk about any critical service limits that affect the regular functioning of the Guidance. If the Guidance requires service limit increase, include the service name, limit name and link to the service quotas page.>

### Supported Regions (if applicable)

<If the Guidance is built for specific AWS Regions, or if the services used in the Guidance do not support all Regions, please specify the Region this Guidance is best suited for>


## Deployment Steps (required)

Deployment steps must be numbered, comprehensive, and usable to customers at any level of AWS expertise. The steps must include the precise commands to run, and describe the action it performs.

* All steps must be numbered.
* If the step requires manual actions from the AWS console, include a screenshot if possible.
* The steps must start with the following command to clone the repo. ```git clone xxxxxxx```
* If applicable, provide instructions to create the Python virtual environment, and installing the packages using ```requirement.txt```.
* If applicable, provide instructions to capture the deployed resource ARN or ID using the CLI command (recommended), or console action.


**Example:**

1. Clone the repo using command ```git clone xxxxxxxxxx```
2. cd to the repo folder ```cd <repo-name>```
3. Install packages in requirements using command ```pip install requirement.txt```
4. Edit content of **file-name** and replace **s3-bucket** with the bucket name in your account.
5. Run this command to deploy the stack ```cdk deploy```
6. Capture the domain name created by running this CLI command ```aws apigateway ............```



## Deployment Validation  (required)

<Provide steps to validate a successful deployment, such as terminal output, verifying that the resource is created, status of the CloudFormation template, etc.>


**Examples:**

* Open CloudFormation console and verify the status of the template with the name starting with xxxxxx.
* If deployment is successful, you should see an active database instance with the name starting with <xxxxx> in        the RDS console.
*  Run the following CLI command to validate the deployment: ```aws cloudformation describe xxxxxxxxxxxxx```



## Running the Guidance (required)

<Provide instructions to run the Guidance with the sample data or input provided, and interpret the output received.>

This section should include:

* Guidance inputs
* Commands to run
* Expected output (provide screenshot if possible)
* Output description



## Next Steps (required)

Provide suggestions and recommendations about how customers can modify the parameters and the components of the Guidance to further enhance it according to their requirements.


Cleanup
-------
Please kick ·cdk destroy· to clean up the whole environment.

FAQ, known issues, additional considerations, and limitations
-------------------------------------------------------------
N/A
Revisions
---------
N/A
Notices
=======
During the launch of this reference architecture,
you will install software (and dependencies) on the Amazon EC2 instances launched
in your account via stack creation.
The software packages and/or sources you will install
will be from the Amazon Linux distribution, as well as from third party sites.
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

