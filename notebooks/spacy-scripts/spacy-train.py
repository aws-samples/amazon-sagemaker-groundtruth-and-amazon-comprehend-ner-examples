import argparse
import os
from itertools import chain
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict

# Make spacy.convert & spacy.train output plain log.
os.environ["ANSI_COLORS_DISABLE"] = "1"
os.environ["WASABI_NO_PRETTY"] = "1"
os.environ["WASABI_LOG_FRIENDLY"] = "1"

# Additional setting for spacy.train to make its log plain.
os.environ["LOG_FRIENDLY"] = "1"

# For the plain log setting to take effect, import spacy only after the env. vars.
from spacy.cli import convert, train  # isort:skip  # noqa:E402


def parse_hyperparameters(hm) -> Dict[str, Any]:
    """Convert list of ['--name', 'value', ...] to { 'name': value}, where 'value' is converted to the nearest data type.

    Conversion follows the principle: "if it looks like a duck and quacks like a duck, then it must be a duck".
    """
    d = {}

    it = iter(hm)
    try:
        while True:
            key = next(it)[2:]
            value = next(it)
            d[key] = value
    except StopIteration:
        pass

    # Infer data types.
    dd = {k: infer_dtype(v) for k, v in d.items()}
    return dd


def infer_dtype(s):
    """Auto-cast string values to nearest matching datatype.

    Conversion follows the principle: "if it looks like a duck and quacks like a duck, then it must be a duck".

    Note that python 3.6 implements PEP-515 which allows '_' as thousand separators. Hence, on Python 3.6,
    '1_000' is a valid number and will be converted accordingly.
    """
    if s == "None":
        return None
    if s == "True":
        return True
    if s == "False":
        return False

    try:
        i = float(s)
        if ("." in s) or ("e" in s.lower()):
            return i
        else:
            return int(s)
    except:  # noqa:E722
        pass

    return s


def assert_train_args(args):
    locked_args = {"lang", "pipeline", "output_path", "train_path", "dev_path"}
    violation = set(args) & locked_args
    if len(violation) > 0:
        raise ValueError(f"Error: overriden args {violation} in locked args {locked_args}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Minimum args according to SageMaker protocol.
    parser.add_argument("--model_dir", type=Path, default=os.environ.get("SM_MODEL_DIR", "model"))
    parser.add_argument("--train", type=Path, default=os.environ.get("SM_CHANNEL_TRAIN", "train"))
    parser.add_argument("--test", type=Path, default=os.environ.get("SM_CHANNEL_TEST", "test"))

    args, train_args = parser.parse_known_args()

    # Convert each .iob file and save the output .json to the same channel. We can do this because spacy.cli.train
    # loads only .json or .jsonl in a given directory (see spacy/gold.pyx: walk_corpus()).
    for iob_path in chain(args.train.glob("*.iob"), args.test.glob("*.iob")):
        convert(
            input_file=iob_path,
            output_dir=iob_path.parent,
            converter="iob",
            model="en_core_web_sm",
            seg_sents=True,
            n_sents=10,
        )

    # Start training
    hyperopts = parse_hyperparameters(train_args)
    assert_train_args(hyperopts)
    print("spacy train with hyperparameters", hyperopts)
    train(lang="en", pipeline="ner", output_path=args.model_dir, train_path=args.train, dev_path=args.test, **hyperopts)

    # model.tar.gz to contain just model-final/.
    # And just fyi., after training, model_dir/ will contains: model-final/, model-best/, model0/, model1/, ...
    for d in args.model_dir.iterdir():
        if d.name == "model-final":
            continue
        rmtree(d)
