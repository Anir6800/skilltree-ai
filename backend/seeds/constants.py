"""
Seed Constants — SkillTree AI
================================
Deterministic category hierarchy, difficulty tiers, and XP scaling tables.
All values are static and produce identical output on every seed run.
"""

# ---------------------------------------------------------------------------
# Category Hierarchy
# ---------------------------------------------------------------------------

CATEGORIES = {
    "ds": "Data Structures",
    "algorithms": "Algorithms",
    "aiml": "AI / ML",
    "webdev": "Web Development",
    "databases": "Databases",
    "sysdesign": "System Design",
    "devops": "DevOps",
    "problemsolving": "Problem Solving",
    "productux": "Product & UX",
}

SUBCATEGORIES = {
    "ds": [
        "Arrays & Strings",
        "Linked Lists",
        "Stacks & Queues",
        "Trees & BSTs",
        "Graphs",
    ],
    "algorithms": [
        "Sorting",
        "Binary Search",
        "Recursion",
        "Dynamic Programming",
        "Greedy Techniques",
    ],
    "aiml": [
        "ML Basics",
        "Feature Engineering",
        "Model Evaluation",
        "Neural Networks",
        "LLM Prompting",
    ],
    "webdev": [
        "HTML/CSS Foundations",
        "JavaScript DOM",
        "React Components",
        "Django REST APIs",
        "Auth & Routing",
    ],
    "databases": [
        "SQL Queries",
        "Schema Design",
        "Indexes",
        "Transactions",
        "PostgreSQL Tuning",
    ],
    "sysdesign": [
        "Scalability Basics",
        "Caching",
        "Queues",
        "WebSockets",
        "Observability",
    ],
    "devops": [
        "Git Workflow",
        "Docker",
        "CI/CD",
        "Linux CLI",
        "Deployments",
    ],
    "problemsolving": [
        "Complexity Analysis",
        "Pattern Recognition",
        "Debugging",
        "Test Design",
        "Edge Cases",
    ],
    "productux": [
        "Information Architecture",
        "Accessibility",
        "Motion Design",
        "Responsive Layouts",
        "User Flows",
    ],
}

# ---------------------------------------------------------------------------
# Difficulty / XP Scaling Tables
# ---------------------------------------------------------------------------

DIFFICULTY_TIERS = {
    1: {"label": "Beginner", "xp_base": 50, "unlock_xp": 0, "est_minutes": 15},
    2: {"label": "Novice", "xp_base": 100, "unlock_xp": 100, "est_minutes": 25},
    3: {"label": "Intermediate", "xp_base": 175, "unlock_xp": 300, "est_minutes": 35},
    4: {"label": "Advanced", "xp_base": 275, "unlock_xp": 600, "est_minutes": 50},
    5: {"label": "Expert", "xp_base": 400, "unlock_xp": 1000, "est_minutes": 60},
}

# Difficulty multiplier mapping for quests (maps difficulty 1-5 to multiplier)
QUEST_DIFFICULTY_MULTIPLIERS = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
    4: 3.0,
    5: 4.0,
}

# ---------------------------------------------------------------------------
# Quest Families
# ---------------------------------------------------------------------------

QUEST_FAMILIES = [
    "data_structures",
    "algorithms",
    "aiml",
    "webdev",
    "databases",
    "sysdesign",
    "devops",
    "debugging_testing",
    "product_ux",
    "fullstack_integration",
]

# ---------------------------------------------------------------------------
# Embedding / Vector Metadata Constants
# ---------------------------------------------------------------------------

EMBEDDING_COLLECTION = "skill_knowledge"
CHROMA_ID_PREFIX = "seed"
