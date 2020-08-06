from asyncio import AbstractEventLoop
from datetime import datetime


def get_loop_time(loop: AbstractEventLoop, time: datetime) -> float:
    seconds_till_time = time.timestamp() - datetime.now().timestamp()
    return loop.time() + seconds_till_time
