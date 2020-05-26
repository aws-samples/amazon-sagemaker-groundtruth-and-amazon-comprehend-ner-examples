import pytest
from aws_lambda_context import (
    LambdaClientContext,
    LambdaClientContextMobileClient,
    LambdaCognitoIdentity,
    LambdaContext,
)

from converter import app


@pytest.fixture()
def apigw_event():
    """Generates S3 Event"""
    return {
        "Records": [
            {
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "bucket": {"name": "vm-gtner-blog"},
                    "object": {"key": "output.manifest"},
                }
            }
        ]
    }


@pytest.fixture()
def lambda_ctx() -> LambdaContext:
    lambda_cognito_identity = LambdaCognitoIdentity()
    lambda_cognito_identity.cognito_identity_id = "cognito_identity_id"
    lambda_cognito_identity.cognito_identity_pool_id = "cognito_identity_pool_id"

    lambda_client_context_mobile_client = LambdaClientContextMobileClient()
    lambda_client_context_mobile_client.installation_id = "installation_id"
    lambda_client_context_mobile_client.app_title = "app_title"
    lambda_client_context_mobile_client.app_version_name = "app_version_name"
    lambda_client_context_mobile_client.app_version_code = "app_version_code"
    lambda_client_context_mobile_client.app_package_name = "app_package_name"

    lambda_client_context = LambdaClientContext()
    lambda_client_context.client = lambda_client_context_mobile_client
    lambda_client_context.custom = {"custom": True}
    lambda_client_context.env = {"env": "test"}

    lambda_context = LambdaContext()
    lambda_context.function_name = "function_name"
    lambda_context.function_version = "function_version"
    lambda_context.invoked_function_arn = "invoked_function_arn"
    lambda_context.memory_limit_in_mb = 1234
    lambda_context.aws_request_id = "aws_request_id"
    lambda_context.log_group_name = "log_group_name"
    lambda_context.log_stream_name = "log_stream_name"
    lambda_context.identity = lambda_cognito_identity
    lambda_context.client_context = lambda_client_context

    return lambda_context


def test_lambda_handler(apigw_event, lambda_ctx: LambdaContext):
    ret = app.lambda_handler(apigw_event, lambda_ctx)
    print(ret)
    assert "s3fs" in ret["metadata"]
