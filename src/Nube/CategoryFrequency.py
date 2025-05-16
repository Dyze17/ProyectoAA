from collections import defaultdict

class CategoryFrequency:
    def __init__(self):
        self.frequencies = defaultdict(lambda: defaultdict(int))

    def increment(self, category: str, variable: str):
        self.frequencies[category][variable.lower()] += 1

    def get_frequencies(self):
        return self.frequencies
