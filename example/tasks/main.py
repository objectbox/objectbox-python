import time
from cmd import Cmd
from objectbox import Entity, Date, Id, String, Store

@Entity()
class Task:
    id = Id()
    text = String()
    date_created = Date(py_type=int)
    date_finished = Date(py_type=int)


# Objectbox expects date timestamp in milliseconds since UNIX epoch
def now_ms() -> int:
    return int(time.time_ns() / 1000000)


def format_date(timestamp_ms: int) -> str:
    return "" if timestamp_ms == 0 else time.ctime(timestamp_ms / 1000)


class TasklistCmd(Cmd):
    prompt = "> "

    def __init__(self):
        super().__init__()
        self._store = Store(directory="tasklist-db")
        self._task_box = self._store.box(Task)
        self._query = self._task_box.query().build()

    def add_task(self, text: str):
        task = Task(text=text, date_created=now_ms())
        self._task_box.put(task)

    def remove_task(self, task_id: int) -> bool:
        is_removed = self._task_box.remove(task_id)
        return is_removed

    def find_tasks(self):
        query = self._task_box.query().build()
        return query.find()

    # *** Command line ***

    def do_ls(self, _):
        """ Lists all the tasks created. """
        tasks = self.find_tasks()

        print("%3s  %-29s  %-29s  %s" % ("ID", "Created", "Finished", "Text"))
        for task in tasks:
            print("%3d  %-29s  %-29s  %s" % (
                task.id, format_date(task.date_created), format_date(task.date_finished), task.text))

    def do_new(self, text: str):
        """ Creates a new task with the given text (all arguments concatenated). """
        self.add_task(text)

    def do_done(self, task_id: str):
        """ Marks the task with the given ID as done. """
        if not task_id.isdigit() or int(task_id) <= 0:
            print(f"Invalid task ID: \"{task_id}\"")
            return
        task = self._task_box.get(int(task_id))
        if task is None:
            print(f"Task {task_id} not found")
            return
        task.date_finished = now_ms()
        self._task_box.put(task)

    def do_rm(self, task_id: str):
        """ Removes a task given its ID. """
        if not task_id.isdigit() or int(task_id) <= 0:
            print(f"Invalid task ID: \"{task_id}\"")
            return
        is_removed = self.remove_task(int(task_id))
        if not is_removed:
            print(f"Task {task_id} not found")

    def do_exit(self, _):
        """ Closes the program. """
        raise SystemExit()


if __name__ == '__main__':
    app = TasklistCmd()
    app.cmdloop('Welcome to the ObjectBox tasks-list app example. Type help or ? for a list of commands.')
