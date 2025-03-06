import numpy as np
from enum import Enum
import os, json
from box import Box
from ruamel.yaml import YAML
from sqlalchemy import MetaData


class ScoreMode(Enum):
    """Different ways we might consider scoring our runs. This is for BO's sake, not for our RL agent -
    ie helps us decide which hyper combos to pursue."""
    MEAN = 1  # mean of all episodes
    LAST = 2  # final episode (the one w/o killing)
    POS = 3  # max # positive tests
    CONSECUTIVE_POS = 4  # max # *consecutive* positives
    TOTAL = 5
    MIX = 6


def calculate_score(scores, MODE='mean', threshold=None):
    for i, a in enumerate(scores):
        if a == 0.: scores[i] = -1.
    if MODE == 'mean':
        return np.mean(scores)
    elif MODE == 'threshold_mean':
        # The idea behind this is that the first 'threshold' episodes are for learning and then
        # we start computing return
        scores = list(scores)
        return np.mean(scores[threshold:])
    elif MODE == 'last':
        return scores[-1]
    elif MODE == 'mix':
        return np.mean(scores[:-1]) + scores[-1]
    elif MODE == 'pos':
        return sum(1 for x in scores if x > 0)
    elif MODE == 'total':
        return sum(x for x in scores)
    elif MODE == 'consecutive_pos':
        score, curr_consec = 0, 0
        for i, adv in enumerate(scores):
            if adv > 0:
                curr_consec += 1
                continue
            if curr_consec > score:
                score = curr_consec
            curr_consec = 0
        return score


def add_common_args(parser):
    parser.add_argument('-g', '--gpu-split', type=float, default=1, help="Num ways we'll split the GPU (how many tabs you running?)")
    parser.add_argument('--autoencode', action="store_true", help="If you're running out of GPU memory, try --autoencode which scales things down")


last_good_commit = '6a6e49c'


def network_spec(hypers):
    """Builds an array of dicts that conform to TForce's network specification (see their docs) by mix-and-matching
    different network hypers
    """
    net = Box(hypers['net'])
    batch_norm = {"type": "tf_layer", "layer": "batch_normalization"}
    arr = []

    def add_dense(s):
        dense = {
            'size': s,
            'l2_regularization': net.l2,
            #'l1_regularization': net.l1
        }
        if not net.batch_norm:
            arr.append({'type': 'dense', 'activation': net.activation, **dense})
            return
        arr.append({'type': 'linear', **dense})
        arr.append(batch_norm)
        arr.append({'type': 'nonlinearity', 'name': net.activation})
        # FIXME dense dropout bug https://github.com/reinforceio/tensorforce/issues/317
        if net.dropout: arr.append({'type': 'dropout', 'rate': net.dropout})

    # Mid-layer
    for i in range(net.depth_mid):
        arr.append({
            'size': net.width,
            'window': (net.kernel_size, 1),
            'stride': (net.stride, 1),
            'type': 'conv2d',
            # 'bias': net.bias,
            'l2_regularization': net.l2,
#            'l1_regularization': net.l1
        })
    arr.append({'type': 'flatten'})

    # Post Dense layers
    if net.flat_dim:
        fc_dim = net.width * (net.step_window / (net.depth_mid * net.stride))
    else:
        fc_dim = net.width * 4
    for i in range(net.depth_post):
        size = fc_dim / (i + 1) if net.funnel else fc_dim
        add_dense(int(size))

    return arr


def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)

def dump_sqlalchemy(engine):
    """ Returns the entire content of a database as lists of dicts"""

    meta = MetaData()
    meta.reflect(bind=engine)  # http://docs.sqlalchemy.org/en/rel_0_9/core/reflection.html
    result = {}
    for table in meta.sorted_tables:
        result[table.name] = [dict(row) for row in engine.execute(table.select())]
    return json.dumps(result)


def create_net(num_layers, size, window, stride, funnel, reg, dropout):
    net = list()
    if funnel:
        a = 1
        b = 2
    else:
        a = b = 1

    side_layer = {"type": "conv2d",
                  "size": 2 ** size,
                  "window": window,
                  "stride": stride,
                  "activation": "relu",
                  "l2_regularization": reg,
                  "dropout": dropout}
    mid_layer = {"type": "conv2d",
                 "size": 2 ** (size + a),
                 "window": window,
                 "stride": stride,
                 "activation": "relu",
                 "l2_regularization": reg,
                  "dropout": dropout}
    central_layer = {"type": "conv2d",
                     "size": 2 ** (size + b),
                     "window": window,
                     "stride": stride,
                     "activation": "relu",
                     "l2_regularization": reg,
                     "dropout": dropout}

    flatten = {"type": "flatten"}

    dense = {"type": "dense",
             "size": 2 ** (size + a + b),
             "activation": "sigmoid",
             "l2_regularization": reg}

    _num = int(num_layers / 5)
    _res = num_layers % 5

    if _res > 0:
        net.append(side_layer)
    if _res == 3:
        net.append(side_layer)

    for i in range(_num):
        net.append(side_layer)

    if _res == 4:
        net.append(mid_layer)

    for i in range(_num):
        net.append(mid_layer)
    for i in range(_num):
        net.append(central_layer)
    for i in range(_num):
        net.append(mid_layer)

    if _res == 4:
        net.append(mid_layer)

    for i in range(_num):
        net.append(side_layer)

    if _res == 2:
        net.append(side_layer)

    net.append(flatten)
    net.append(dense)

    return net

def raise_refactor():
    raise NotImplemented(f'Restore from {last_good_commit}')