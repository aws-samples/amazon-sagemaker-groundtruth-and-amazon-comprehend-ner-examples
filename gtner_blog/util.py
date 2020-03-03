import xmlrpc.client
from typing import Iterable, Iterator, List

import s3fs

################################################################################
# Data utilities
################################################################################
# Default
_fs = s3fs.S3FileSystem(anon=False)

Token_t = str
Sentence_t = List[Token_t]


class SplitRecord(object):
    def __init__(self, group: int, sentence: Sentence_t):
        self.group = group
        self.sentence = sentence

    def __iter__(self):
        return iter((self.group, self.sentence))


def sentences(it: Iterable[Token_t]) -> Iterator[Sentence_t]:
    """Group .iob tokens into sentences.

    This function assumes .iob file does not contain document marker -DOCSTART-.

    Args:
        it ([str]): tokens from an .iob file

    Yields:
        [str]: list of tokens from a sentence
    """
    sentence = []
    for line in it:
        line = line.rstrip()
        if line == "":
            yield sentence
            sentence = []
        else:
            sentence.append(line)

    # Don't forget the last sentence still in the buffer.
    if len(sentence) > 0:
        yield sentence


def split(it: Iterable[Sentence_t]) -> Iterator[SplitRecord]:
    """Split an .iob located in S3, into train:test = 3:1 splits.

    Yields:
        (int, [str]): A tuple where int denotes split group, and [str] is a list of tokens from
            a sentence.
    """
    for i, sentence in enumerate(sentences(it)):
        split_group = 0 if (i % 3) < 2 else 1
        yield SplitRecord(split_group, sentence)


def write_split(it: SplitRecord, *args):
    """Write each sentence in `it` to either the train S3 object or the test S3 object.

    Args:
        it (tuple): tuple (int, [str]) where int denotes split group, and [str] is a list of
            tokens from a sentence.
        *args (list of strings): list of filenames, each correspond to a split group
    """
    with _fs.open(args[0], "w") as f_train:
        with _fs.open(args[1], "w") as f_test:
            f_handle = [f_train, f_test]
            for split, sentence in it:
                f = f_handle[split]
                f.write("\n".join(sentence))
                f.write("\n\n")  # 1x \n for the last token, and 1x \n as a sentence separator


def bilou2bio(it: Iterable[Token_t]) -> Iterator[str]:
    """For each line, convert its BILOU tag to a BIO tag.

    Assume that the last field is the NER tag.
    """
    conversion_table = {"L": "I", "U": "B"}
    for line in it:
        try:
            i = line.rindex(" ") + 1
        except:
            yield line
        else:
            c = line[i]
            line = line[:i] + conversion_table.get(c, c) + line[i + 1 :]
            yield line


class LabelCollector(object):
    def __init__(self):
        self._labels = set()

    @property
    def labels(self):
        """Get the unique labels seen so far."""
        return set(self._labels)

    @property
    def sorted_labels(self):
        """Get the sorted unique labels seen so far"""
        return sorted(list(self._labels))

    def __call__(self, it: Iterable[str]) -> Iterator[str]:
        """Observe the label in each line, then yield the line as it is."""
        for line in it:
            try:
                i = line.rindex(" ") + 1
            except:
                pass
            else:
                self._labels.add(line[i:].rstrip())
            yield line
