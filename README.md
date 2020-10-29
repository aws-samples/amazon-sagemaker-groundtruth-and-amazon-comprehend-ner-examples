# Companion Codes for AWS Blog Post *Developing NER models with Amazon SageMaker Ground Truth and Amazon Comprehend*

**Update October 2020:** *Amazon Comprehend now supports Amazon SageMaker
GroundTruth to help label your datasets for Comprehend's Custom Model training.
For Custom EntityRecognizer, checkout [Annotations](https://docs.aws.amazon.com/comprehend/latest/dg/cer-annotation.html)
documentation for more details. For Custom MultiClass and MultiLabel Classifier,
checkout [MultiClass](https://docs.aws.amazon.com/comprehend/latest/dg/how-document-classification-training-multi-class.html)
and [MultiLabel](https://docs.aws.amazon.com/comprehend/latest/dg/how-document-classification-training-multi-label.html)
documentation for more details respectively.*

This repository contains the source CloudFormation template that the [blog post]()
uses to setup the data conversion pipeline, and sample corpus.

It is recommended to deploy a stack by following the instructions contained in
the [blog post](). Once the stack is deployed, you can then upload the sample
corpus to your new bucket.

We also recommend that you check out <https://github.com/aws-samples/amazon-comprehend-examples/>
which contains:

1. the source module used by the Lambda function in this repository, and

2. the `convertGroundtruthToComprehendERFormat.sh` script to parse the
   augmented output manifest file and create the annotations and documents file
   in CSV format accepted by Amazon Comprehend.

# Deployment from source template

To still deploy your stack using the source template in this repository, rather
than the one-click deployment described in the [blog post](), please follow
these steps:

1. Build Lambda layer: on your EC2 instance, run `bin/build-lambda-layer-s3fs-p38.sh`.
   Upload the resulted zip file `lambda-layer-s3fs-p38.zip` to your S3.

2. Update `CloudFormation/template.yaml`, specifically resource `S3fsP38Layer`
   to point to the layer file from step 1. After modifications, it should look
   like this:

   ```yaml
    S3fsP38Layer:
      Type: AWS::Lambda::LayerVersion
      Properties:
        ...
        Content:
          S3Bucket: <your_s3_bucket_to_host_lambda_layer>
          S3Key: <your_s3_key_to_the_layer_zip>
        ...
   ```

3. Package and upload the CloudFormation template to your S3. Make sure that you
   deploy to the same region as the layer zip's S3 location.

    ```bash
    cd CloudFormation/

    aws  cloudformation package --template-file template.yaml --s3-bucket <value> --s3-prefix <value> --output-template-file cfn.yaml

    aws cloudformation deploy --template-file cfn.yaml --capabilities CAPABILITY_IAM --stack-name <value> --parameter-overrides BucketName=<your_s3_bucket>
    ```

# License Summary

This sample code is made available under the MIT-0 License. See the LICENSE file.
