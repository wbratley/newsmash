import aws_cdk as cdk
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_secretsmanager as secretsmanager,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_iam as iam,
    CfnOutput,
    Duration,
    RemovalPolicy,
)
from constructs import Construct


class NewshashStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── DynamoDB cache table ──────────────────────────────────────────────
        cache_table = dynamodb.Table(
            self,
            "CacheTable",
            table_name="newshash-cache",
            partition_key=dynamodb.Attribute(
                name="pk", type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="ttl",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ── Secrets Manager — API key ─────────────────────────────────────────
        # After first deploy, set the value with:
        #   aws secretsmanager put-secret-value \
        #     --secret-id newshash/anthropic-api-key \
        #     --secret-string "sk-ant-..."
        api_key_secret = secretsmanager.Secret(
            self,
            "AnthropicApiKey",
            secret_name="newshash/anthropic-api-key",
            description="Anthropic API key for Newshash",
        )

        # ── Shared Lambda environment ─────────────────────────────────────────
        shared_env = {
            "ANTHROPIC_API_KEY_SECRET_ARN": api_key_secret.secret_arn,
            "CACHE_TABLE_NAME": cache_table.table_name,
        }

        # ── Container image (built from Dockerfile.lambda in project root) ────
        image_code = lambda_.DockerImageCode.from_image_asset(
            "..",
            file="Dockerfile.lambda",
        )

        # ── API Lambda — serves HTTP requests via API Gateway ─────────────────
        api_fn = lambda_.DockerImageFunction(
            self,
            "ApiFunction",
            code=image_code,
            memory_size=1024,
            # API Gateway hard limit is 29 s; cache hits are <1 s.
            # Cold-start generation (cache miss) may still timeout on first run
            # of the day — the scheduler below prevents that in normal operation.
            timeout=Duration.seconds(29),
            environment=shared_env,
        )

        # ── Scheduler Lambda — pre-generates digest daily, bypasses GW timeout ─
        scheduler_fn = lambda_.DockerImageFunction(
            self,
            "SchedulerFunction",
            code=image_code,
            memory_size=1024,
            timeout=Duration.minutes(10),
            environment=shared_env,
            # Override the default CMD to point at the scheduler handler.
            cmd=["app.lambda_scheduler.handler"],
        )

        # Grant both functions access to DynamoDB and Secrets Manager.
        for fn in (api_fn, scheduler_fn):
            cache_table.grant_read_write_data(fn)
            api_key_secret.grant_read(fn)

        # ── EventBridge rule — run scheduler daily at 07:00 UTC ──────────────
        events.Rule(
            self,
            "DailySchedule",
            schedule=events.Schedule.cron(minute="0", hour="7"),
            targets=[events_targets.LambdaFunction(scheduler_fn)],
        )

        # ── API Gateway (REST) with throttling ────────────────────────────────
        api = apigw.LambdaRestApi(
            self,
            "Api",
            handler=api_fn,
            proxy=True,
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                # Sustained: 2 req/s, burst: 10 req/s
                throttling_rate_limit=2,
                throttling_burst_limit=10,
            ),
        )

        # ── CloudFront distribution ───────────────────────────────────────────
        # Sits in front of API Gateway for HTTPS, global CDN, and an extra
        # caching layer. Content is already cached in DynamoDB so CloudFront
        # caching is disabled here; enable it in the cache policy below if you
        # want CloudFront to absorb repeat hits without touching Lambda at all.
        api_origin_domain = f"{api.rest_api_id}.execute-api.{self.region}.amazonaws.com"

        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    api_origin_domain,
                    origin_path="/prod",
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                # Disable CloudFront caching — DynamoDB handles freshness.
                # To let CloudFront cache daily HTML and skip Lambda entirely,
                # swap this for a custom policy with default_ttl=Duration.hours(12).
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
            ),
        )

        # ── Outputs ───────────────────────────────────────────────────────────
        CfnOutput(self, "AppUrl",
                  value=f"https://{distribution.distribution_domain_name}",
                  description="Newshash public URL (CloudFront)")
        CfnOutput(self, "ApiGatewayUrl",
                  value=api.url,
                  description="Direct API Gateway URL (for debugging)")
        CfnOutput(self, "SecretArn",
                  value=api_key_secret.secret_arn,
                  description="Set API key: aws secretsmanager put-secret-value --secret-id newshash/anthropic-api-key --secret-string sk-ant-...")
        CfnOutput(self, "CacheTableName",
                  value=cache_table.table_name)
