"""CPU-fit cap retains all observed classes and reports which records were fitted.

These tests use synthetic record stubs and do not claim medical validity.
"""
from types import SimpleNamespace
from collections import Counter

from backend.labs import _select_training_subset


def _ordered_records():
    # Simulate a MedMNIST-style class-sorted dataset with very rare final labels.
    counts=[900,850,800,450,240,70,1]
    return [SimpleNamespace(index=j,label=str(label))
            for label,n in enumerate(counts)
            for j in range(sum(counts[:label]),sum(counts[:label+1]))]


def test_training_cap_keeps_every_label_in_sorted_input():
    rows=_ordered_records()
    assert len(rows)>2400
    picked=_select_training_subset(rows,max_train=2400,seed=42)
    assert len(picked)==2400
    counts=Counter(s.label for s in picked)
    assert len(counts)==7
    assert counts['6']==1
    assert len({s.index for s in picked})==2400
    assert [s.index for s in picked]==sorted(s.index for s in picked)


def test_training_subset_reproducible_and_untruncated_when_small():
    rows=_ordered_records()
    picked=_select_training_subset(rows,max_train=2400,seed=42)
    repeat=_select_training_subset(rows,max_train=2400,seed=42)
    assert [s.index for s in repeat]==[s.index for s in picked]
    smaller=rows[:100]
    assert _select_training_subset(smaller,max_train=2400,seed=42)==smaller
