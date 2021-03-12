#!/usr/bin/env python3.8
from resolvers import router, logger

logger.setLevel("DEBUG")


def handler(event, _):
    logger.debug(event)

    res = router.resolve(event)
    logger.debug(f"RESULT: {res.value}")

    return res
