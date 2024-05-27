from cmd import Cmd
from objectbox import *
import time

@Entity()
class Task:
    id = Id()
    text = String()

    date_created = Date(py_type=int)
    date_finished = Date(py_type=int)



# objectbox expects date timestamp in milliseconds since UNIX epoch
def now_ms() -> int:
    return time.time_ns() / 1000000


def format_date(timestamp_ms: int) -> str:
    return "" if timestamp_ms == 0 else time.ctime(timestamp_ms / 1000)


class TasklistCmd(Cmd):
    prompt = "> "
    _store = Store(directory="tasklist-db")
    _box = _store.box(Task)

    def do_ls(self, _):
        """list tasks"""

        tasks = self._box.get_all()

        print("%3s  %-29s  %-29s  %s" % ("ID", "Created", "Finished", "Text"))
        for task in tasks:
            print("%3d  %-29s  %-29s  %s" % (
            task.id, format_date(task.date_created), format_date(task.date_finished), task.text))

    def do_new(self, text: str):
        """create a new task with the given text (all arguments concatenated)"""
        task = Task()
        task.text = text
        task.date_created = now_ms()
        self._box.put(task)

    def do_done(self, id: str):
        """mark task with the given ID as done"""
        task = self._box.get(int(id))
        task.date_finished = now_ms()
        self._box.put(task)

    def do_exit(self, _):
        """close the program"""
        raise SystemExit()


if __name__ == '__main__':
    app = TasklistCmd()
    app.cmdloop('Welcome to the ObjectBox tasks-list app example. Type help or ? for a list of commands.')
