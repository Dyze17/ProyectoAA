from VariableCategory import VariableCategory

def load_variable_categories(filepath):
    category_map = {}

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            header = file.readline()  # Omitir encabezado
            for line in file:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(",", 1)
                if len(parts) < 2:
                    print(f"⚠ Línea ignorada por formato inválido: {line}")
                    continue

                category = parts[0].strip()
                terms = parts[1].strip().split(" - ")
                main_term = terms[0].lower()
                synonyms = [t.strip().lower() for t in terms]

                if category not in category_map:
                    category_map[category] = VariableCategory(category)
                category_map[category].add_variable(main_term, synonyms)

    except Exception as e:
        print(f"❌ Error al cargar categorías: {e}")

    return list(category_map.values())


def load_abstracts(filepath):
    abstracts = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        entries = content.split("@")
        for entry in entries:
            if "abstract" in entry.lower():
                lines = entry.split("\n")
                abstract_lines = []
                for line in lines:
                    if "abstract" in line.lower():
                        abstract = line.split("=", 1)[-1].strip().strip("{}").strip()
                        abstract_lines.append(abstract)
                if abstract_lines:
                    abstracts.append(" ".join(abstract_lines))

    except Exception as e:
        print(f"❌ Error al cargar abstracts: {e}")

    return abstracts