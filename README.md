# Companion Codes for AWS Blog Post "Developing NER models on Amazon SageMaker"

20200519:

- v1.x is the version with Spacy and huggingface transformers. This is now
  tracked on a separate branch named `spacy-and-transformers`.
- Moving forwards, the `master` branch replaces these custom algorithms with
  Comprehend Custom NER.

This repository contains the source CloudFormation template that the blog post
uses to setup the data conversion pipeline, and sample corpus.

It is recommended to deploy a stack by following the instructions contained in
the blog post. Once the stack is deployed, you can then upload the sample corpus
to your new bucket.

To still deploy everything from this repository:

```bash
cd CloudFormation/
aws cloudformation package --template-file template.yaml --s3-bucket <value> --s3-prefix <value> --output-template-file cfn.yaml
aws deploy --template-file cfn.yaml --stack-name <value>
```

## License Summary

This sample code is made available under the MIT-0 License. See the LICENSE file.
