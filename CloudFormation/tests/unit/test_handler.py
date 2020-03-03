import pytest

from gtam2conll2003 import app


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


def test_lambda_handler(apigw_event, mocker):
    ret = app.lambda_handler(apigw_event, "")
    print(ret)
    assert ("s3fs" in ret) and ("spacy" in ret)
