# Companion Codes for AWS Blog Post "Developing NER models on Amazon SageMaker"

This repository contains the source CloudFormation template that the blog post
uses to setup the data conversion pipeline, a notebook instance populated with
two NER-training notebooks, and upload sample corpus to an S3 bucket.

It is recommended to deploy a stack by following the instructions contained in
the blog post.

To still deploy everything from this repository:

```bash
cd CloudFormation/
aws cloudformation package --template-file template.yaml --s3-bucket <value> --s3-prefix <value> --output-template-file cfn.yaml
aws deploy --template-file cfn.yaml --stack-name <value>
```

## License Summary
This sample code is made available under the MIT-0 License. See the LICENSE file.
