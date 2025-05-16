class VariableCategory:
    def __init__(self, category):
        self.category = category
        self.variable_map = {}  # main_term (str) -> list of synonyms (List[str])

    def add_variable(self, main_term, synonyms):
        self.variable_map[main_term.lower()] = synonyms

    def get_category(self):
        return self.category

    def get_variable_map(self):
        return self.variable_map
