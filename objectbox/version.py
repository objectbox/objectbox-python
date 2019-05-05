class Version:
    def __init__(self, major: int, minor: int, patch: int, label: str = ""):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.label = label

    def __str__(self):
        result = ".".join(map(str, [self.major, self.minor, self.patch]))
        if len(self.label) > 0:
            result += "-" + self.label
        return result
