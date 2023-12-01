from __future__ import annotations

import logging
import signal
import sys
from inspect import FrameInfo


def main():
    # TODO in case if one of steps(while putting "necessary data" failed
    #  that step must rerun
    pass


def sigint_handler(sig: int, frame: FrameInfo.frame):
    sys.tracebacklimit = 0
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    logging.basicConfig(
        filemode="a+", format='%(asctime)s %(levelname)s %(message)s',
        level=logging.INFO,
    )
    main()
