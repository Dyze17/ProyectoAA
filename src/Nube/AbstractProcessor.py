from typing import List
from CategoryFrequency import CategoryFrequency
from VariableCategory import VariableCategory

class AbstractProcessor:
    def __init__(self, categories: List[VariableCategory]):
        self.categories = categories
        self.frequency = CategoryFrequency()

    def process_abstracts(self, abstracts: List[str]):
        for abs_text in abstracts:
            abs_text = abs_text.lower()
            for category in self.categories:
                for main_term, synonyms in category.get_variable_map().items():
                    for synonym in synonyms:
                        if synonym.strip().lower() in abs_text:
                            self.frequency.increment(category.get_category(), main_term)
                            break  # Evitar contar múltiples sinónimos del mismo término

    def get_frequency(self):
        return self.frequency
