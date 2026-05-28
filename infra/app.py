#!/usr/bin/env python3
import os
import aws_cdk as cdk
from newsmash_stack import NewsmashStack

app = cdk.App()
NewsmashStack(
    app,
    "NewsmashStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "eu-west-2"),
    ),
)
app.synth()
