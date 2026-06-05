TECH_CHIPSET = {

    "Python": [
        "FastAPI",
        "Django",
        "Flask",
        "Pandas",
        "NumPy",
        "LangChain",
        "LangGraph"
    ],

    "FastAPI": [
        "Python",
        "REST API",
        "AsyncIO"
    ],

    "Spring": [
        "Spring Boot",
        "JPA",
        "Hibernate",
        "Java"
    ],

    "MySQL": [
        "SQL",
        "Database",
        "RDBMS"
    ],

    "LangChain": [
        "LLM",
        "RAG",
        "Prompt Engineering"
    ],

    "LangGraph": [
        "Agent",
        "Workflow",
        "LLM"
    ]
}

def expand_skills(skills):

    expanded = set()

    for skill in skills:

        expanded.add(skill)

        related_skills = TECH_CHIPSET.get(
            skill,
            []
        )

        expanded.update(
            related_skills
        )

    return list(expanded)