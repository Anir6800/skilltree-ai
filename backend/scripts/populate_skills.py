"""
SkillTree AI - Sample Skill Data Population Script
Run this script to populate the database with sample skills for testing.

Usage:
    python manage.py shell < scripts/populate_skills.py
"""

from skills.models import Skill, SkillPrerequisite

# Clear existing data (optional - comment out if you want to keep existing data)
print("Clearing existing skills...")
SkillPrerequisite.objects.all().delete()
Skill.objects.all().delete()

# Create skills
print("Creating skills...")

# Algorithms Category
binary_search = Skill.objects.create(
    title="Binary Search",
    description="Master the art of efficient searching in sorted arrays using the divide-and-conquer approach.",
    category="algorithms",
    difficulty=2,
    xp_required_to_unlock=0
)

sorting_basics = Skill.objects.create(
    title="Sorting Algorithms",
    description="Learn fundamental sorting algorithms including bubble sort, insertion sort, and selection sort.",
    category="algorithms",
    difficulty=2,
    xp_required_to_unlock=50
)

quicksort = Skill.objects.create(
    title="QuickSort & MergeSort",
    description="Advanced sorting algorithms with O(n log n) complexity. Essential for technical interviews.",
    category="algorithms",
    difficulty=3,
    xp_required_to_unlock=150
)

dynamic_programming = Skill.objects.create(
    title="Dynamic Programming",
    description="Solve complex problems by breaking them down into simpler subproblems. Master memoization and tabulation.",
    category="algorithms",
    difficulty=4,
    xp_required_to_unlock=300
)

# Data Structures Category
arrays_basics = Skill.objects.create(
    title="Arrays & Lists",
    description="Foundation of data structures. Learn array manipulation, traversal, and common operations.",
    category="ds",
    difficulty=1,
    xp_required_to_unlock=0
)

linked_lists = Skill.objects.create(
    title="Linked Lists",
    description="Master singly and doubly linked lists. Learn insertion, deletion, and reversal operations.",
    category="ds",
    difficulty=2,
    xp_required_to_unlock=100
)

stacks_queues = Skill.objects.create(
    title="Stacks & Queues",
    description="LIFO and FIFO data structures. Essential for BFS, DFS, and expression evaluation.",
    category="ds",
    difficulty=2,
    xp_required_to_unlock=100
)

trees = Skill.objects.create(
    title="Binary Trees",
    description="Hierarchical data structures. Learn traversals, BST operations, and tree properties.",
    category="ds",
    difficulty=3,
    xp_required_to_unlock=200
)

graphs = Skill.objects.create(
    title="Graph Theory",
    description="Master graph representations, traversals (BFS/DFS), and shortest path algorithms.",
    category="ds",
    difficulty=4,
    xp_required_to_unlock=350
)

# Systems Category
os_basics = Skill.objects.create(
    title="Operating Systems Basics",
    description="Understand processes, threads, memory management, and file systems.",
    category="systems",
    difficulty=2,
    xp_required_to_unlock=0
)

networking = Skill.objects.create(
    title="Computer Networks",
    description="Learn TCP/IP, HTTP, DNS, and network protocols. Essential for backend development.",
    category="systems",
    difficulty=3,
    xp_required_to_unlock=150
)

databases = Skill.objects.create(
    title="Database Systems",
    description="Master SQL, database design, indexing, and query optimization.",
    category="systems",
    difficulty=3,
    xp_required_to_unlock=200
)

# Web Dev Category
html_css = Skill.objects.create(
    title="HTML & CSS",
    description="Foundation of web development. Learn semantic HTML and modern CSS techniques.",
    category="webdev",
    difficulty=1,
    xp_required_to_unlock=0
)

javascript = Skill.objects.create(
    title="JavaScript Fundamentals",
    description="Master ES6+, async/await, promises, and modern JavaScript features.",
    category="webdev",
    difficulty=2,
    xp_required_to_unlock=100
)

react = Skill.objects.create(
    title="React Development",
    description="Build modern web applications with React. Learn hooks, state management, and component patterns.",
    category="webdev",
    difficulty=3,
    xp_required_to_unlock=250
)

backend_apis = Skill.objects.create(
    title="REST API Development",
    description="Design and build RESTful APIs. Learn authentication, validation, and best practices.",
    category="webdev",
    difficulty=3,
    xp_required_to_unlock=250
)

# AI/ML Category
python_basics = Skill.objects.create(
    title="Python Programming",
    description="Master Python fundamentals, data structures, and object-oriented programming.",
    category="aiml",
    difficulty=1,
    xp_required_to_unlock=0
)

numpy_pandas = Skill.objects.create(
    title="NumPy & Pandas",
    description="Data manipulation and analysis with Python. Essential for data science and ML.",
    category="aiml",
    difficulty=2,
    xp_required_to_unlock=100
)

machine_learning = Skill.objects.create(
    title="Machine Learning Basics",
    description="Learn supervised and unsupervised learning. Master regression, classification, and clustering.",
    category="aiml",
    difficulty=3,
    xp_required_to_unlock=300
)

deep_learning = Skill.objects.create(
    title="Deep Learning",
    description="Neural networks, CNNs, RNNs, and transformers. Build AI models with PyTorch or TensorFlow.",
    category="aiml",
    difficulty=4,
    xp_required_to_unlock=500
)

# Create prerequisites (edges in the graph)
print("Creating prerequisites...")

# Algorithms prerequisites
SkillPrerequisite.objects.create(from_skill=arrays_basics, to_skill=binary_search)
SkillPrerequisite.objects.create(from_skill=arrays_basics, to_skill=sorting_basics)
SkillPrerequisite.objects.create(from_skill=sorting_basics, to_skill=quicksort)
SkillPrerequisite.objects.create(from_skill=quicksort, to_skill=dynamic_programming)

# Data Structures prerequisites
SkillPrerequisite.objects.create(from_skill=arrays_basics, to_skill=linked_lists)
SkillPrerequisite.objects.create(from_skill=arrays_basics, to_skill=stacks_queues)
SkillPrerequisite.objects.create(from_skill=linked_lists, to_skill=trees)
SkillPrerequisite.objects.create(from_skill=trees, to_skill=graphs)
SkillPrerequisite.objects.create(from_skill=stacks_queues, to_skill=graphs)

# Systems prerequisites
SkillPrerequisite.objects.create(from_skill=os_basics, to_skill=networking)
SkillPrerequisite.objects.create(from_skill=os_basics, to_skill=databases)

# Web Dev prerequisites
SkillPrerequisite.objects.create(from_skill=html_css, to_skill=javascript)
SkillPrerequisite.objects.create(from_skill=javascript, to_skill=react)
SkillPrerequisite.objects.create(from_skill=javascript, to_skill=backend_apis)

# AI/ML prerequisites
SkillPrerequisite.objects.create(from_skill=python_basics, to_skill=numpy_pandas)
SkillPrerequisite.objects.create(from_skill=numpy_pandas, to_skill=machine_learning)
SkillPrerequisite.objects.create(from_skill=machine_learning, to_skill=deep_learning)

# Cross-category prerequisites
SkillPrerequisite.objects.create(from_skill=arrays_basics, to_skill=python_basics)
SkillPrerequisite.objects.create(from_skill=databases, to_skill=backend_apis)

print("\n✅ Successfully created:")
print(f"   - {Skill.objects.count()} skills")
print(f"   - {SkillPrerequisite.objects.count()} prerequisites")
print("\n🎉 Sample data population complete!")
print("\nSkills by category:")
for category, name in Skill.CATEGORY_CHOICES:
    count = Skill.objects.filter(category=category).count()
    print(f"   - {name}: {count} skills")
