from collections import defaultdict
from typing import List
from VariableCategory import VariableCategory

class CoOccurrenceMatrix:
    def __init__(self):
        self.matrix = defaultdict(lambda: defaultdict(int))
        self.all_terms = set()

    def process_abstracts(self, abstracts: List[str], categories: List[VariableCategory]):
        for abs_text in abstracts:
            abs_text = abs_text.lower()
            terms_found = set()

            for category in categories:
                for main_term, synonyms in category.get_variable_map().items():
                    main_term = main_term.lower()
                    for synonym in synonyms:
                        if synonym.strip().lower() in abs_text:
                            terms_found.add(main_term)
                            self.all_terms.add(main_term)
                            break

            terms_found = list(terms_found)
            for i in range(len(terms_found)):
                for j in range(i + 1, len(terms_found)):
                    t1, t2 = terms_found[i], terms_found[j]
                    self.matrix[t1][t2] += 1
                    self.matrix[t2][t1] += 1  # Simetría

    def get_matrix(self):
        return self.matrix

    def get_all_terms(self):
        return sorted(self.all_terms)
