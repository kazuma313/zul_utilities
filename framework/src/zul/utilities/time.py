"""Dipindahkan ke `zul.utilities.script_helper.eval_performance`.

File ini dipertahankan supaya import lama tetap jalan:
    from zul.utilities.time import TimerDecorator
"""

from .script_helper.eval_performance import TimerDecorator, timer_func

__all__ = ["TimerDecorator", "timer_func"]
