#!/usr/bin/env python3
import os
import aws_cdk as cdk
from newshash_stack import NewshashStack

app = cdk.App()
NewshashStack(
    app,
    "NewshashStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "eu-west-2"),
    ),
)
app.synth()
