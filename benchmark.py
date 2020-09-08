import objectbox
import time
from tests.model import TestEntity
from tests.common import remove_test_dir, load_empty_test_objectbox


class ObjectBoxPerf:
    """
    Performance executable
    """

    def __init__(self):
        self.ob = load_empty_test_objectbox()
        self.box = objectbox.Box(self.ob, TestEntity)

    def remove_all(self):
        self.box.remove_all()

    def put_many(self, items):
        self.box.put(items)

    def read_all(self):
        return self.box.get_all()


class Timer:
    """
    Context manager to time a block of code.
    Appends the resulting runtime in milliseconds to a list of floats.
    """

    def __init__(self, out_list: [float]):
        self.start = time.time_ns()
        self.list = out_list

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.list.append((time.time_ns() - self.start) / 1000 / 1000)


class PerfExecutor:
    """
    Performance executable
    """

    def __init__(self, executable):
        self.perf = executable

    def run(self, count=1000, runs=10):
        inserts = self.__prepare_data(count)

        # function => vector of runtimes in milliseconds
        from collections import defaultdict
        times = defaultdict(list)

        progress_text = "Measuring performance"
        for i in range(runs):
            self.__progress_bar(progress_text, i, runs)

            with Timer(times["insert-many"]):
                self.perf.put_many(inserts)

            with Timer(times["read-all"]):
                items = self.perf.read_all()

            with Timer(times["update-many"]):
                self.perf.put_many(items)

            with Timer(times["remove-all"]):
                self.perf.remove_all()

        self.__progress_bar(progress_text, runs, runs)

        # print the results
        print()
        print('=' * 80)
        print("runs\t%d\t\tcount\t%d\t\tunit\tms" % (runs, count))
        print("Function\tMedian\tMean\tStdDev")
        import statistics
        for key in times.keys():
            print("%s\t%d\t%d\t%d" % (
                key,
                statistics.median(times[key]),
                statistics.mean(times[key]),
                statistics.stdev(times[key])
            ))

    @staticmethod
    def __prepare_data(count: int) -> [TestEntity]:
        result = []
        for i in range(count):
            object = TestEntity()
            object.str = "Entity no. %d" % i
            object.float = i * 1.1
            object.int = i
            result.append(object)
        return result

    @staticmethod
    def __progress_bar(text, value, endvalue, bar_length=20):
        import sys
        percent = float(value) / endvalue
        arrow = '-' * int(round(percent * bar_length) - 1) + '>'
        spaces = ' ' * (bar_length - len(arrow))

        sys.stdout.write("\r{0}: [{1}] {2}%".format(text, arrow + spaces, int(round(percent * 100))))
        sys.stdout.flush()


if __name__ == "__main__":
    remove_test_dir()

    obPerf = ObjectBoxPerf()
    executor = PerfExecutor(obPerf)
    executor.run(count=10000, runs=20)

    remove_test_dir()
