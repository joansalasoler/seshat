import asyncio
import logging, threading
from typing import Any, TYPE_CHECKING
from collections.abc import Iterable
from gi.repository import GLib, GObject

from seshat.tasks.task_context import TaskContext

if TYPE_CHECKING:
    from seshat.application import Command


_logger = logging.getLogger(__name__)


class TaskExecutor(GObject.Object):
    """Executes tasks asynchronously"""

    __gtype_name__ = "TaskExecutor"

    __gsignals__ = {
        "on-task-success": (
            GObject.SignalFlags.RUN_LAST, None, (object,)),

        "on-task-error": (
            GObject.SignalFlags.RUN_LAST, None, (object,))
    }

    def __init__(self) -> None:
        super().__init__()
        self._task: asyncio.Task | None = None
        self._event_loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def is_running(self) -> bool:
        """Check if a task is currently running."""

        return (
            self._task is not None and
            not self._task.done()
        )

    def submit(self, command: "Command", query: str, text: str) -> None:
        """Submit a task for execution."""

        self.cancel_task()
        ctx = TaskContext(command, query, text)
        self._task = asyncio.run_coroutine_threadsafe(
            self._process_task(ctx), self._event_loop
        )

    def cancel_task(self) -> None:
        """Cancel the currently running task if one exists."""

        if self._task and not self._task.done():
            self._task.cancel()

    def shutdown(self) -> None:
        """Shutdown the executor."""

        self.cancel_task()
        self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        self._thread.join()

    def _run_loop(self) -> None:
        """Run the event loop in a separate thread."""

        try:
            asyncio.set_event_loop(self._event_loop)
            self._event_loop.run_forever()
        except Exception as e:
            _logger.error("Event loop error: %s", e)
        finally:
            self._event_loop.close()

    async def _process_task(self, task: TaskContext) -> None:
        """Process a task asynchronously."""

        try:
            result = await task.command.invoke(task.query, task.text)
            task.result = result

            if not isinstance(task.result, str):
                values = list([str(r) for r in task.result])
                task.result = values[0] if len(values) == 1 else values

            if len(task.result) < 1 or not str(task.result).strip():
                task.error = "Task did not return a result"
        except asyncio.CancelledError:
            task.cancelled = True
        except Exception as e:
            task.error = str(e)

        if not task.cancelled:
            self._emit_task_completion(task)

    def _emit_task_completion(self, task: TaskContext) -> None:
        """Emit completion of a task"""

        has_error = task.error is not None
        signal = "on-task-error" if has_error else "on-task-success"
        callback = lambda: self.emit(signal, task)
        GLib.idle_add(callback)
