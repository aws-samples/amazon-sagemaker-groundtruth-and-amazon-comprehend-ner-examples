from boto3.session import Session
import os
import json
from typing import Any, Dict, List

import s3fs
import spacy
from spacy.gold import biluo_tags_from_offsets

ENTITY_T = Dict[str, Any]
DEFAULT_ATTR = "ner"
fs = s3fs.S3FileSystem(anon=False)
s3_client = Session().client("s3")
# Used for replacing invalid characters in tag values
trs = str.maketrans("$[]", "___")


def lambda_handler(event, context):
    s3_event = event["Records"][0]["s3"]
    input_file = f"s3://{s3_event['bucket']['name']}/{s3_event['object']['key']}"
    output_file = input_file[:-8] + "iob"  # Rename output.manifest to output.iob
    print("input_file, output_file =", (input_file, output_file))

    # Add tags to output.manifest to simply user in tracking the conversion
    # execution.
    add_tags(
        bucket=s3_event["bucket"]["name"],
        obj=s3_event["object"]["key"],
        tags={
            f"lambda_req_id": context.aws_request_id,
            f"lambda_log_group": context.log_group_name,
            f"lambda_log_stream": context.log_stream_name.translate(trs),
        },
    )

    converter = Conll2003Converter(doc_sep=False)
    with fs.open(output_file, "w") as f:
        for line in converter(input_file):
            f.write(f"{line}\n")

    return {m.__name__: m.__version__ for m in (spacy, s3fs)}


def add_tags(bucket: str, obj: str, tags: Dict[str, str]) -> List[Dict[str, str]]:
    """Tag the object with `tag_key = tag_value`."""
    # NOTE: `put_object_tagging()` overwrites existing tags set with a new set.
    # Hence, we do a write-after-read of tag sets to append new tags.

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


def open(path: str):
    """Iterate over deserialized JSON Lines in an augmented manifest."""
    with fs.open(path, "r") as f:
        yield from (json.loads(line) for line in f)


class Conll2003Converter(object):
    """Convert augmented manifest to conll-2003 format."""

    valid_codecs = {"bilou", "bio"}

    def __init__(self, lang: str = "en", codec: str = "bilou", doc_sep: bool = False):
        """Create a converter that converts an augmented manifest to conll-2003 format.

        By default, do not emit document separators (i.e., `DOCSTART`) as many NER modules ignore them. Even SpaCy turns
        it off by default.

        Args:
            lang (str, optional): ISO 639-1 code of the language class to load as a tokenizer. Defaults to "en".
            codec (str, optional): tagging scheme to use, either 'bilou' or 'bio'. The tagging scheme can have mixed
                cases, and characters being shuffled. Defaults to 'bilou'.
            doc_sep (bool, optional): whether to yield from ["-DOCSTART- -X- O O", ""]. Defaults to False.
        """
        self.nlp = spacy.blank(lang)
        self.doc_sep = doc_sep
        self.codec = "".join(sorted(codec.lower()))
        if self.codec not in self.valid_codecs:
            raise ValueError("Invalid codec: " + codec)

        if self.codec == "bio":
            self.conversion_table = {"L": "I", "U": "B"}

    def __call__(self, path: str):
        r"""Convert augmented manifest format to conll-2003 format.

        Args:
            fname (str or Path): input filename

        Yields:
            str: each line in the conll-2003 format (without \n at the end)
        """
        has_seen_doc = False
        for doc_json in open(path):
            if has_seen_doc:
                yield ""
            has_seen_doc = True
            if self.doc_sep:
                # Emit document marker
                yield "-DOCSTART- -X- O O"
                yield ""

            # Convert augmented manifest annotation to BILUO
            doc = self.nlp(text(doc_json))
            ents = [(e["startOffset"], e["endOffset"], e["label"]) for e in entities(doc_json)]
            biluo_tags = biluo_tags_from_offsets(doc, ents)
            if self.codec == "bilou":
                tags = biluo_tags
            else:
                tags = [self.conversion_table.get(tag[0], tag[0]) + tag[1:] for tag in biluo_tags]

            # Emit entities
            for token, tag in zip(doc, tags):
                if str(token) == "\n":
                    yield ""
                    continue
                # conll2003: word postag chunktag nerlabel
                yield f"{token} _ _ {tag}"

    @staticmethod
    def normalize_codec(codec: str):
        return "".join(sorted(codec.lower()))


def text(d):
    """Get the source text of this document."""
    return d["source"]


def entities(d, sorted=True, attr=DEFAULT_ATTR) -> List[ENTITY_T]:
    """Get entities in each document according to their appearance in the augmented manifest.

    Return values will use the short labels (i.e., shortDisplayName).

    Arguments:
        d {dictionary}: a dictionary deserialized from a JSON Line in an augmented manifest.

    Keyword Arguments:
        sorted {bool}: whether to sort by starting offset or leave it according to the order entities appear in
            augmented file (default: {True})
        attr {str}: (default: {ner})

    Returns:
        [type] -- [description]
    """
    retval = []
    txt = d["source"]
    entities = d[attr]["annotations"]["entities"]
    scores = d[f"{attr}-metadata"]["entities"]
    types = {pair["label"]: pair["shortDisplayName"] for pair in d[attr]["annotations"]["labels"]}
    for ent, conf in zip(entities, scores):
        # NOTE: [start, end)
        start, end = ent["startOffset"], ent["endOffset"]

        retval.append(
            {
                "words": txt[start:end],
                "label": types[ent["label"]],
                "startOffset": start,
                "endOffset": end,
                "confidence": conf["confidence"],
            }
        )

    if sorted:
        retval.sort(key=lambda x: x["startOffset"])

    return retval
