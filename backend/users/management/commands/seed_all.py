"""
Master seed command for SkillTree AI.
Runs all seed steps in dependency order:
  1. Skills (skill tree nodes + prerequisites)
  2. Quests (linked to skills)
  3. Badges (achievement definitions)

Usage:
    python manage.py seed_all
    python manage.py seed_all --only skills
    python manage.py seed_all --only quests
    python manage.py seed_all --only badges
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


SEED_STEPS = ['skills', 'quests', 'badges']


class Command(BaseCommand):
    help = 'Seed all initial data: skills, quests, and badges'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only',
            choices=SEED_STEPS,
            default=None,
            help='Run only a specific seed step',
        )

    def handle(self, *args, **options):
        only = options.get('only')
        steps = [only] if only else SEED_STEPS

        self.stdout.write(self.style.MIGRATE_HEADING('\n🌱 SkillTree AI — Seed Runner'))

        if 'skills' in steps:
            self.stdout.write('\n📚 Seeding skills...')
            self._seed_skills()

        if 'quests' in steps:
            self.stdout.write('\n🎯 Seeding quests...')
            self._seed_quests()

        if 'badges' in steps:
            self.stdout.write('\n🏅 Seeding badges...')
            call_command('add_badges', verbosity=0)
            self.stdout.write(self.style.SUCCESS('  ✓ Badges seeded'))

        self.stdout.write(self.style.SUCCESS('\n✅ All seed steps complete.\n'))

    def _seed_skills(self):
        from skills.models import Skill, SkillPrerequisite

        skills_data = [
            {"title": "Binary Search", "category": "algorithms", "difficulty": 2, "xp_required_to_unlock": 0,
             "description": "Master efficient searching in sorted arrays using divide-and-conquer."},
            {"title": "Sorting Algorithms", "category": "algorithms", "difficulty": 2, "xp_required_to_unlock": 50,
             "description": "Learn bubble sort, insertion sort, and selection sort."},
            {"title": "QuickSort & MergeSort", "category": "algorithms", "difficulty": 3, "xp_required_to_unlock": 150,
             "description": "Advanced O(n log n) sorting algorithms essential for interviews."},
            {"title": "Dynamic Programming", "category": "algorithms", "difficulty": 4, "xp_required_to_unlock": 300,
             "description": "Solve complex problems via memoization and tabulation."},
            {"title": "Arrays & Lists", "category": "ds", "difficulty": 1, "xp_required_to_unlock": 0,
             "description": "Foundation of data structures: array manipulation and traversal."},
            {"title": "Linked Lists", "category": "ds", "difficulty": 2, "xp_required_to_unlock": 100,
             "description": "Singly and doubly linked lists: insertion, deletion, reversal."},
            {"title": "Stacks & Queues", "category": "ds", "difficulty": 2, "xp_required_to_unlock": 100,
             "description": "LIFO and FIFO structures for BFS, DFS, and expression evaluation."},
            {"title": "Binary Trees", "category": "ds", "difficulty": 3, "xp_required_to_unlock": 200,
             "description": "Hierarchical structures: traversals, BST operations, tree properties."},
            {"title": "Graph Theory", "category": "ds", "difficulty": 4, "xp_required_to_unlock": 350,
             "description": "Graph representations, BFS/DFS, and shortest path algorithms."},
            {"title": "Operating Systems Basics", "category": "systems", "difficulty": 2, "xp_required_to_unlock": 0,
             "description": "Processes, threads, memory management, and file systems."},
            {"title": "Computer Networks", "category": "systems", "difficulty": 3, "xp_required_to_unlock": 150,
             "description": "TCP/IP, HTTP, DNS, and network protocols."},
            {"title": "Database Systems", "category": "systems", "difficulty": 3, "xp_required_to_unlock": 200,
             "description": "SQL, database design, indexing, and query optimization."},
            {"title": "HTML & CSS", "category": "webdev", "difficulty": 1, "xp_required_to_unlock": 0,
             "description": "Semantic HTML and modern CSS techniques."},
            {"title": "JavaScript Fundamentals", "category": "webdev", "difficulty": 2, "xp_required_to_unlock": 100,
             "description": "ES6+, async/await, promises, and modern JavaScript."},
            {"title": "React Development", "category": "webdev", "difficulty": 3, "xp_required_to_unlock": 250,
             "description": "React hooks, state management, and component patterns."},
            {"title": "REST API Development", "category": "webdev", "difficulty": 3, "xp_required_to_unlock": 250,
             "description": "Design and build RESTful APIs with auth and validation."},
            {"title": "Python Programming", "category": "aiml", "difficulty": 1, "xp_required_to_unlock": 0,
             "description": "Python fundamentals, data structures, and OOP."},
            {"title": "NumPy & Pandas", "category": "aiml", "difficulty": 2, "xp_required_to_unlock": 100,
             "description": "Data manipulation and analysis for data science and ML."},
            {"title": "Machine Learning Basics", "category": "aiml", "difficulty": 3, "xp_required_to_unlock": 300,
             "description": "Supervised/unsupervised learning: regression, classification, clustering."},
            {"title": "Deep Learning", "category": "aiml", "difficulty": 4, "xp_required_to_unlock": 500,
             "description": "Neural networks, CNNs, RNNs, and transformers."},
        ]

        skill_map = {}
        created = 0
        for data in skills_data:
            title = data['title']
            obj, was_created = Skill.objects.get_or_create(title=title, defaults=data)
            skill_map[title] = obj
            if was_created:
                created += 1

        prerequisites = [
            ("Arrays & Lists", "Binary Search"),
            ("Arrays & Lists", "Sorting Algorithms"),
            ("Sorting Algorithms", "QuickSort & MergeSort"),
            ("QuickSort & MergeSort", "Dynamic Programming"),
            ("Arrays & Lists", "Linked Lists"),
            ("Arrays & Lists", "Stacks & Queues"),
            ("Linked Lists", "Binary Trees"),
            ("Binary Trees", "Graph Theory"),
            ("Stacks & Queues", "Graph Theory"),
            ("Operating Systems Basics", "Computer Networks"),
            ("Operating Systems Basics", "Database Systems"),
            ("HTML & CSS", "JavaScript Fundamentals"),
            ("JavaScript Fundamentals", "React Development"),
            ("JavaScript Fundamentals", "REST API Development"),
            ("Python Programming", "NumPy & Pandas"),
            ("NumPy & Pandas", "Machine Learning Basics"),
            ("Machine Learning Basics", "Deep Learning"),
            ("Arrays & Lists", "Python Programming"),
            ("Database Systems", "REST API Development"),
        ]

        prereq_created = 0
        for from_title, to_title in prerequisites:
            f = skill_map.get(from_title)
            t = skill_map.get(to_title)
            if f and t:
                _, was_created = SkillPrerequisite.objects.get_or_create(from_skill=f, to_skill=t)
                if was_created:
                    prereq_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {created} skills created, {prereq_created} prerequisites linked'
        ))

    def _seed_quests(self):
        from skills.models import Skill
        from quests.models import Quest

        def get_skill(title):
            try:
                return Skill.objects.get(title=title)
            except Skill.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠ Skill '{title}' not found — run seed_all --only skills first"))
                return None

        def safe_create(skill, **kwargs):
            if skill is None:
                return
            title = kwargs.get('title')
            Quest.objects.get_or_create(title=title, skill=skill, defaults={'skill': skill, **kwargs})

        arrays = get_skill("Arrays & Lists")
        python_skill = get_skill("Python Programming")
        binary_search_skill = get_skill("Binary Search")
        sorting_skill = get_skill("Sorting Algorithms")
        dp_skill = get_skill("Dynamic Programming")
        linked_list_skill = get_skill("Linked Lists")
        stacks_skill = get_skill("Stacks & Queues")
        trees_skill = get_skill("Binary Trees")

        if arrays:
            safe_create(arrays, type='coding', title='Two Sum',
                description='Return indices of two numbers that add up to target.',
                starter_code='def two_sum(nums, target):\n    pass\n',
                test_cases=[{"input": "4 2 7 11 15 9", "expected_output": "[0, 1]"}],
                xp_reward=100, estimated_minutes=15, difficulty_multiplier=1.0)
            safe_create(arrays, type='coding', title='Maximum Subarray',
                description='Find the contiguous subarray with the largest sum.',
                starter_code='def max_subarray(nums):\n    pass\n',
                test_cases=[{"input": "-2 1 -3 4 -1 2 1 -5 4", "expected_output": "6"}],
                xp_reward=120, estimated_minutes=20, difficulty_multiplier=2.0)

        if python_skill:
            safe_create(python_skill, type='coding', title='FizzBuzz',
                description='Print FizzBuzz for numbers 1 to N.',
                starter_code='def fizzbuzz(n):\n    pass\n',
                test_cases=[{"input": "15", "expected_output": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz"}],
                xp_reward=50, estimated_minutes=10, difficulty_multiplier=1.0)

        if binary_search_skill:
            safe_create(binary_search_skill, type='coding', title='Classic Binary Search',
                description='Return index of target in sorted array, -1 if not found.',
                starter_code='def binary_search(nums, target):\n    pass\n',
                test_cases=[{"input": "6 -1 0 3 5 9 12 9", "expected_output": "4"}],
                xp_reward=150, estimated_minutes=20, difficulty_multiplier=2.0)

        if dp_skill:
            safe_create(dp_skill, type='coding', title='Fibonacci with Memoization',
                description='Compute Nth Fibonacci number using dynamic programming.',
                starter_code='def fib(n, memo={}):\n    pass\n',
                test_cases=[{"input": "10", "expected_output": "55"}],
                xp_reward=200, estimated_minutes=25, difficulty_multiplier=3.0)

        if stacks_skill:
            safe_create(stacks_skill, type='coding', title='Valid Parentheses',
                description='Determine if bracket string is valid.',
                starter_code='def is_valid(s):\n    pass\n',
                test_cases=[{"input": "()[]{}", "expected_output": "True"}],
                xp_reward=150, estimated_minutes=20, difficulty_multiplier=2.0)

        total = Quest.objects.count()
        self.stdout.write(self.style.SUCCESS(f'  ✓ Quests seeded — {total} total in database'))
