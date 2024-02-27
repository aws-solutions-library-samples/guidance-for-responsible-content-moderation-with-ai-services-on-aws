#!/usr/bin/env python3
try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk
from stacks.chaliceapp import ChaliceApp

app = cdk.App()

stage = 'workshop'

ChaliceApp(app, 'image-moderation-' + stage, stage, description='Image Moderation Workshop (SO9407)')

app.synth()
