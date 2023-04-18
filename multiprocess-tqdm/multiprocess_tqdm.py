#!/usr/bin/env python3

import sys
import multiprocessing
from tqdm.auto import tqdm


def worker(mapper, sequence, rank, return_dict):
    result = []
    for value in tqdm(sequence, desc="PROC {}".format(rank), position=rank, file=sys.stdout):
        result.append(mapper(value))
    return_dict[rank] = result


def map_with_tqdm(mapper, sequence, num_proc):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    ps = []
    try:
        for i in range(num_proc):
            p = multiprocessing.Process(
                target=worker,
                args=(mapper, sequence[i::num_proc], i, return_dict)
            )
            ps.append(p)
            p.start()
    finally:
        for p in ps:
            p.join()
    result = [None] * len(sequence)
    for i in range(num_proc):
        result[i::num_proc] = return_dict[i]
    return result
