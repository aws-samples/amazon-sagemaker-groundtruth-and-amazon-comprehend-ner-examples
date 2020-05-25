import csv
import json
from typing import Dict, List, Optional

import boto3
import botocore
import s3fs

fs = s3fs.S3FileSystem(anon=False)
s3_client = boto3.session.Session().client("s3")

# Used for replacing invalid characters in tag values
trs = str.maketrans("$[]", "___")


def lambda_handler(event, context):
    s3_event = event["Records"][0]["s3"]
    input_file = f"s3://{s3_event['bucket']['name']}/{s3_event['object']['key']}"
    data_file = input_file[:-8] + "txt"
    ann_file = input_file[:-8] + "csv"
    print("input_file, data_file, ann_file =", (input_file, data_file, ann_file))

    # Add tags to output.manifest to track conversion execution.
    add_tags(
        bucket=s3_event["bucket"]["name"],
        obj=s3_event["object"]["key"],
        tags={
            "lambda_req_id": context.aws_request_id,
            "lambda_log_group": context.log_group_name,
            "lambda_log_stream": context.log_stream_name.translate(trs),
        },
        s3_client=s3_client,
    )

    # Start conversions.
    with fs.open(input_file, "r") as f_gt, fs.open(data_file, "w") as f_data, fs.open(ann_file, "w") as f_ann:
        datawriter = csv.writer(f_data)
        annwriter = csv.writer(f_ann)
        annwriter.writerow(["File", "Line", "Begin Offset", "End Offset", "Type"])

        # Process each line in Ground Truth's output manifest.
        for index, jsonLine in enumerate(f_gt):
            source = GT2Comprehend.convert_to_dataset(jsonLine)
            datawriter.writerow([source])

            annotations = GT2Comprehend.convert_to_annotations(index, jsonLine)
            for entry in annotations:
                annwriter.writerow(entry)

    return {
        "files": {"input_file": input_file, "data_file": data_file, "ann_file": ann_file},
        "lambda": {
            "lambda_req_id": context.aws_request_id,
            "lambda_log_group": context.log_group_name,
            "lambda_log_stream_raw": context.log_stream_name,
            "lambda_log_stream_trs": context.log_stream_name.translate(trs),
        },
        "metadata": {m.__name__: m.__version__ for m in (s3fs, boto3)},
    }


def add_tags(
    bucket: str, obj: str, tags: Dict[str, str], s3_client: Optional[botocore.client.S3] = None
) -> List[Dict[str, str]]:
    """Tag the object with `tag_key = tag_value`."""
    # NOTE: `put_object_tagging()` overwrites existing tags set with a new set.
    # Hence, we do a write-after-read of tag sets to append new tags.

    if s3_client is None:
        s3_client = boto3.session.Session().client("s3")

    # Fetch existing tags. For the format of the response message, see
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_object_tagging
    existing_tags: List[Dict[str, str]] = s3_client.get_object_tagging(Bucket=bucket, Key=obj)["TagSet"]

    # If there's existing tag, then we have to remove the old one, otherwise
    # put_object_tagging() complains about multiple tags with the same key.
    existing_tags2 = [d for d in existing_tags if d["Key"] not in tags]

    # Append new tag to existing tags
    new_tags = existing_tags2 + [{"Key": tag_key, "Value": tag_value} for tag_key, tag_value in tags.items()]

    # Put new tags to the S3 object.
    s3_client.put_object_tagging(Bucket=bucket, Key=obj, Tagging={"TagSet": new_tags})

    return new_tags


class GT2Comprehend(object):
    @staticmethod
    def convert_to_dataset(self, jsonLine):
        jsonObj = self.parse_manifest_input(jsonLine)
        return jsonObj["source"]

    @staticmethod
    def convert_to_annotations(self, index, jsonLine):
        annotations = []
        jsonObj = self.parse_manifest_input(jsonLine)
        self.labeling_job_name = self.get_labeling_job_name(jsonObj)
        number_of_labels = len(jsonObj[self.labeling_job_name]["annotations"]["entities"])
        labeling_job_info = jsonObj[self.labeling_job_name]["annotations"]["entities"]
        for ind in range(number_of_labels):
            annotations.append(
                (
                    self.input_file_name,
                    index,
                    labeling_job_info[ind]["startOffset"],
                    labeling_job_info[ind]["endOffset"],
                    labeling_job_info[ind]["label"].upper(),
                )
            )

        return annotations

    @staticmethod
    def parse_manifest_input(self, jsonLine):
        try:
            jsonObj = json.loads(jsonLine)
            return jsonObj
        except ValueError as e:
            print(f"Error decoding the string: {jsonLine}, {e}")
            raise

    @staticmethod
    def get_labeling_job_name(self, jsonObj):
        for key, value in jsonObj.items():
            if self.is_json_serializable(value):
                if "annotations" in value:
                    job_name = key
        return job_name

    @staticmethod
    def is_json_serializable(self, value):
        try:
            json.dumps(value)
            return True
        except ValueError as e:
            print(e)
            return False
