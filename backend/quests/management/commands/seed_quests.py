"""
Management command to seed skills + quests into the database.
Usage: python manage.py seed_quests
       python manage.py seed_quests --clear   (wipe and re-seed)
"""

from django.core.management.base import BaseCommand
from skills.models import Skill, SkillPrerequisite
from quests.models import Quest


SKILLS = [
    # (title, description, category, difficulty, xp_required)
    ("Arrays & Lists",          "Foundation of data structures. Array manipulation, traversal, and common operations.", "ds",         1, 0),
    ("Python Programming",      "Master Python fundamentals, data structures, and OOP.",                                "aiml",       1, 0),
    ("Binary Search",           "Efficient searching in sorted arrays using divide-and-conquer.",                       "algorithms", 2, 0),
    ("Sorting Algorithms",      "Bubble, insertion, and selection sort fundamentals.",                                  "algorithms", 2, 50),
    ("Dynamic Programming",     "Solve complex problems via memoization and tabulation.",                               "algorithms", 4, 300),
    ("Linked Lists",            "Singly and doubly linked lists — insertion, deletion, reversal.",                      "ds",         2, 100),
    ("Stacks & Queues",         "LIFO and FIFO structures. Essential for BFS, DFS, expression evaluation.",             "ds",         2, 100),
    ("Binary Trees",            "Hierarchical structures. Traversals, BST operations, tree properties.",                "ds",         3, 200),
    ("JavaScript Fundamentals", "Master ES6+, async/await, promises, and modern JS features.",                         "webdev",     2, 100),
    ("QuickSort & MergeSort",   "Advanced O(n log n) sorting algorithms.",                                              "algorithms", 3, 150),
    ("Graph Theory",            "Graph representations, BFS/DFS, shortest path algorithms.",                            "ds",         4, 350),
    ("HTML & CSS",              "Foundation of web development. Semantic HTML and modern CSS.",                         "webdev",     1, 0),
    ("REST API Development",    "Design and build RESTful APIs with auth and validation.",                               "webdev",     3, 250),
    ("NumPy & Pandas",          "Data manipulation and analysis with Python.",                                          "aiml",       2, 100),
    ("Machine Learning Basics", "Supervised/unsupervised learning, regression, classification.",                        "aiml",       3, 300),
]

QUESTS = [
    # ── Arrays ──────────────────────────────────────────────────────────────
    {
        "skill": "Arrays & Lists",
        "type": "coding",
        "title": "Two Sum",
        "description": (
            "Given an array of integers `nums` and an integer `target`, "
            "return the indices of the two numbers that add up to `target`.\n\n"
            "You may assume each input has exactly one solution.\n\n"
            "Example:\n"
            "  Input: 4 2 7 11 15 9\n"
            "  (n=4, nums=[2,7,11,15], target=9)\n"
            "  Output: [0, 1]"
        ),
        "starter_code": (
            "def two_sum(nums, target):\n"
            "    # Your solution here\n"
            "    pass\n\n"
            "line = input().split()\n"
            "n = int(line[0])\n"
            "nums = list(map(int, line[1:n+1]))\n"
            "target = int(line[n+1])\n"
            "print(two_sum(nums, target))\n"
        ),
        "test_cases": [
            {"input": "4 2 7 11 15 9", "expected_output": "[0, 1]"},
            {"input": "3 3 2 4 6",     "expected_output": "[1, 2]"},
            {"input": "2 3 3 6",       "expected_output": "[0, 1]"},
        ],
        "xp_reward": 100, "estimated_minutes": 15, "difficulty_multiplier": 1.0,
    },
    {
        "skill": "Arrays & Lists",
        "type": "coding",
        "title": "Maximum Subarray",
        "description": (
            "Given an integer array `nums`, find the contiguous subarray "
            "with the largest sum and return its sum.\n\n"
            "Example:\n"
            "  Input: -2 1 -3 4 -1 2 1 -5 4\n"
            "  Output: 6\n"
            "  Explanation: [4,-1,2,1] has the largest sum = 6."
        ),
        "starter_code": (
            "def max_subarray(nums):\n"
            "    # Kadane's algorithm\n"
            "    pass\n\n"
            "nums = list(map(int, input().split()))\n"
            "print(max_subarray(nums))\n"
        ),
        "test_cases": [
            {"input": "-2 1 -3 4 -1 2 1 -5 4", "expected_output": "6"},
            {"input": "1",                       "expected_output": "1"},
            {"input": "5 4 -1 7 8",             "expected_output": "23"},
        ],
        "xp_reward": 120, "estimated_minutes": 20, "difficulty_multiplier": 2.0,
    },
    {
        "skill": "Arrays & Lists",
        "type": "debugging",
        "title": "Fix the Reverse Array",
        "description": (
            "The function below is supposed to reverse an array in-place, "
            "but it has a bug. Find and fix it.\n\n"
            "Example:\n"
            "  Input: 1 2 3 4 5\n"
            "  Output: [5, 4, 3, 2, 1]"
        ),
        "starter_code": (
            "def reverse_array(nums):\n"
            "    left, right = 0, len(nums)  # BUG: should be len(nums) - 1\n"
            "    while left < right:\n"
            "        nums[left], nums[right] = nums[right], nums[left]\n"
            "        left += 1\n"
            "        right -= 1\n"
            "    return nums\n\n"
            "nums = list(map(int, input().split()))\n"
            "print(reverse_array(nums))\n"
        ),
        "test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "[5, 4, 3, 2, 1]"},
            {"input": "1 2",       "expected_output": "[2, 1]"},
            {"input": "42",        "expected_output": "[42]"},
        ],
        "xp_reward": 80, "estimated_minutes": 10, "difficulty_multiplier": 1.0,
    },
    # ── Python ───────────────────────────────────────────────────────────────
    {
        "skill": "Python Programming",
        "type": "coding",
        "title": "FizzBuzz",
        "description": (
            "Print numbers from 1 to N.\n"
            "For multiples of 3 print 'Fizz', multiples of 5 print 'Buzz', "
            "both print 'FizzBuzz'.\n\n"
            "Example:\n"
            "  Input: 15\n"
            "  Output: 1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz"
        ),
        "starter_code": (
            "def fizzbuzz(n):\n"
            "    result = []\n"
            "    # Your solution here\n"
            "    return result\n\n"
            "n = int(input())\n"
            "print(' '.join(str(x) for x in fizzbuzz(n)))\n"
        ),
        "test_cases": [
            {"input": "15", "expected_output": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz"},
            {"input": "5",  "expected_output": "1 2 Fizz 4 Buzz"},
            {"input": "1",  "expected_output": "1"},
        ],
        "xp_reward": 50, "estimated_minutes": 10, "difficulty_multiplier": 1.0,
    },
    {
        "skill": "Python Programming",
        "type": "coding",
        "title": "Palindrome Check",
        "description": (
            "Return True if a string is a palindrome, False otherwise.\n"
            "Ignore case and non-alphanumeric characters.\n\n"
            "Example:\n"
            "  Input: racecar\n"
            "  Output: True"
        ),
        "starter_code": (
            "def is_palindrome(s):\n"
            "    # Your solution here\n"
            "    pass\n\n"
            "s = input()\n"
            "print(is_palindrome(s))\n"
        ),
        "test_cases": [
            {"input": "racecar",  "expected_output": "True"},
            {"input": "hello",    "expected_output": "False"},
            {"input": "madam",    "expected_output": "True"},
        ],
        "xp_reward": 75, "estimated_minutes": 15, "difficulty_multiplier": 1.0,
    },
    {
        "skill": "Python Programming",
        "type": "mcq",
        "title": "Python Immutable Types Quiz",
        "description": (
            "Which of the following is an IMMUTABLE data type in Python?\n\n"
            "A) list\n"
            "B) dict\n"
            "C) tuple\n"
            "D) set\n\n"
            "Enter the letter of your answer (A, B, C, or D)."
        ),
        "starter_code": "print(input())\n",
        "test_cases": [
            {"input": "C", "expected_output": "C"},
        ],
        "xp_reward": 30, "estimated_minutes": 5, "difficulty_multiplier": 1.0,
    },
    # ── Binary Search ────────────────────────────────────────────────────────
    {
        "skill": "Binary Search",
        "type": "coding",
        "title": "Classic Binary Search",
        "description": (
            "Given a sorted array and a target, return its index. Return -1 if not found.\n\n"
            "Input format: first number is N (array size), then N numbers, then target.\n\n"
            "Example:\n"
            "  Input: 6 -1 0 3 5 9 12 9\n"
            "  Output: 4"
        ),
        "starter_code": (
            "def binary_search(nums, target):\n"
            "    # Your solution here\n"
            "    pass\n\n"
            "line = input().split()\n"
            "n = int(line[0])\n"
            "nums = list(map(int, line[1:n+1]))\n"
            "target = int(line[n+1])\n"
            "print(binary_search(nums, target))\n"
        ),
        "test_cases": [
            {"input": "6 -1 0 3 5 9 12 9", "expected_output": "4"},
            {"input": "6 -1 0 3 5 9 12 2", "expected_output": "-1"},
            {"input": "1 5 5",             "expected_output": "0"},
        ],
        "xp_reward": 150, "estimated_minutes": 20, "difficulty_multiplier": 2.0,
    },
    {
        "skill": "Binary Search",
        "type": "coding",
        "title": "Search Insert Position",
        "description": (
            "Given a sorted array and a target, return the index if found. "
            "If not, return the index where it would be inserted.\n\n"
            "Example:\n"
            "  Input: 4 1 3 5 6 5 → Output: 2\n"
            "  Input: 4 1 3 5 6 2 → Output: 1"
        ),
        "starter_code": (
            "def search_insert(nums, target):\n"
            "    # Your solution here\n"
            "    pass\n\n"
            "line = input().split()\n"
            "n = int(line[0])\n"
            "nums = list(map(int, line[1:n+1]))\n"
            "target = int(line[n+1])\n"
            "print(search_insert(nums, target))\n"
        ),
        "test_cases": [
            {"input": "4 1 3 5 6 5", "expected_output": "2"},
            {"input": "4 1 3 5 6 2", "expected_output": "1"},
            {"input": "4 1 3 5 6 7", "expected_output": "4"},
        ],
        "xp_reward": 130, "estimated_minutes": 15, "difficulty_multiplier": 2.0,
    },
    # ── Sorting ──────────────────────────────────────────────────────────────
    {
        "skill": "Sorting Algorithms",
        "type": "coding",
        "title": "Bubble Sort Implementation",
        "description": (
            "Implement bubble sort to sort an array in ascending order.\n\n"
            "Input: first number is N, then N integers.\n\n"
            "Example:\n"
            "  Input: 5 5 3 1 4 2\n"
            "  Output: [1, 2, 3, 4, 5]"
        ),
        "starter_code": (
            "def bubble_sort(nums):\n"
            "    n = len(nums)\n"
            "    # Your solution here\n"
            "    return nums\n\n"
            "line = input().split()\n"
            "n = int(line[0])\n"
            "nums = list(map(int, line[1:n+1]))\n"
            "print(bubble_sort(nums))\n"
        ),
        "test_cases": [
            {"input": "5 5 3 1 4 2",          "expected_output": "[1, 2, 3, 4, 5]"},
            {"input": "7 64 34 25 12 22 11 90","expected_output": "[11, 12, 22, 25, 34, 64, 90]"},
            {"input": "1 42",                  "expected_output": "[42]"},
        ],
        "xp_reward": 100, "estimated_minutes": 20, "difficulty_multiplier": 2.0,
    },
    # ── Dynamic Programming ──────────────────────────────────────────────────
    {
        "skill": "Dynamic Programming",
        "type": "coding",
        "title": "Fibonacci with Memoization",
        "description": (
            "Compute the Nth Fibonacci number using dynamic programming.\n\n"
            "F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)\n\n"
            "Example:\n"
            "  Input: 10\n"
            "  Output: 55"
        ),
        "starter_code": (
            "def fib(n, memo={}):\n"
            "    # Your solution here\n"
            "    pass\n\n"
            "n = int(input())\n"
            "print(fib(n))\n"
        ),
        "test_cases": [
            {"input": "10", "expected_output": "55"},
            {"input": "0",  "expected_output": "0"},
            {"input": "20", "expected_output": "6765"},
        ],
        "xp_reward": 200, "estimated_minutes": 25, "difficulty_multiplier": 3.0,
    },
    {
        "skill": "Dynamic Programming",
        "type": "coding",
        "title": "Climbing Stairs",
        "description": (
            "You are climbing N steps. Each time you can climb 1 or 2 steps. "
            "How many distinct ways can you reach the top?\n\n"
            "Example:\n"
            "  Input: 3\n"
            "  Output: 3  (1+1+1, 1+2, 2+1)"
        ),
        "starter_code": (
            "def climb_stairs(n):\n"
            "    # Your solution here\n"
            "    pass\n\n"
            "n = int(input())\n"
            "print(climb_stairs(n))\n"
        ),
        "test_cases": [
            {"input": "2", "expected_output": "2"},
            {"input": "3", "expected_output": "3"},
            {"input": "5", "expected_output": "8"},
        ],
        "xp_reward": 180, "estimated_minutes": 20, "difficulty_multiplier": 3.0,
    },
    # ── Stacks & Queues ──────────────────────────────────────────────────────
    {
        "skill": "Stacks & Queues",
        "type": "coding",
        "title": "Valid Parentheses",
        "description": (
            "Given a string of brackets, determine if it is valid.\n"
            "Open brackets must be closed by the same type in the correct order.\n\n"
            "Example:\n"
            "  Input: ()[]{}\n"
            "  Output: True\n"
            "  Input: (]\n"
            "  Output: False"
        ),
        "starter_code": (
            "def is_valid(s):\n"
            "    # Use a stack\n"
            "    pass\n\n"
            "s = input()\n"
            "print(is_valid(s))\n"
        ),
        "test_cases": [
            {"input": "()[]{}",  "expected_output": "True"},
            {"input": "(]",      "expected_output": "False"},
            {"input": "{[]}",    "expected_output": "True"},
            {"input": "([)]",    "expected_output": "False"},
        ],
        "xp_reward": 150, "estimated_minutes": 20, "difficulty_multiplier": 2.0,
    },
    # ── Linked Lists ─────────────────────────────────────────────────────────
    {
        "skill": "Linked Lists",
        "type": "coding",
        "title": "Reverse a Linked List",
        "description": (
            "Given a singly linked list as space-separated integers, reverse it.\n\n"
            "Example:\n"
            "  Input: 1 2 3 4 5\n"
            "  Output: 5 4 3 2 1"
        ),
        "starter_code": (
            "class ListNode:\n"
            "    def __init__(self, val=0, nxt=None):\n"
            "        self.val = val\n"
            "        self.next = nxt\n\n"
            "def reverse_list(head):\n"
            "    # Your solution here\n"
            "    pass\n\n"
            "def build(vals):\n"
            "    dummy = ListNode()\n"
            "    cur = dummy\n"
            "    for v in vals:\n"
            "        cur.next = ListNode(v)\n"
            "        cur = cur.next\n"
            "    return dummy.next\n\n"
            "def to_list(head):\n"
            "    res = []\n"
            "    while head:\n"
            "        res.append(head.val)\n"
            "        head = head.next\n"
            "    return res\n\n"
            "vals = list(map(int, input().split()))\n"
            "head = build(vals)\n"
            "print(' '.join(map(str, to_list(reverse_list(head)))))\n"
        ),
        "test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "5 4 3 2 1"},
            {"input": "1 2",       "expected_output": "2 1"},
            {"input": "1",         "expected_output": "1"},
        ],
        "xp_reward": 160, "estimated_minutes": 25, "difficulty_multiplier": 2.0,
    },
    # ── Binary Trees ─────────────────────────────────────────────────────────
    {
        "skill": "Binary Trees",
        "type": "coding",
        "title": "Maximum Depth of Binary Tree",
        "description": (
            "Given a binary tree in level-order format (null for missing nodes), "
            "return its maximum depth.\n\n"
            "Example:\n"
            "  Input: 3 9 20 null null 15 7\n"
            "  Output: 3"
        ),
        "starter_code": (
            "from collections import deque\n\n"
            "class TreeNode:\n"
            "    def __init__(self, val=0, left=None, right=None):\n"
            "        self.val = val\n"
            "        self.left = left\n"
            "        self.right = right\n\n"
            "def max_depth(root):\n"
            "    # Your solution here\n"
            "    pass\n\n"
            "def build(vals):\n"
            "    if not vals or vals[0] == 'null': return None\n"
            "    root = TreeNode(int(vals[0]))\n"
            "    q = deque([root])\n"
            "    i = 1\n"
            "    while q and i < len(vals):\n"
            "        node = q.popleft()\n"
            "        if i < len(vals) and vals[i] != 'null':\n"
            "            node.left = TreeNode(int(vals[i]))\n"
            "            q.append(node.left)\n"
            "        i += 1\n"
            "        if i < len(vals) and vals[i] != 'null':\n"
            "            node.right = TreeNode(int(vals[i]))\n"
            "            q.append(node.right)\n"
            "        i += 1\n"
            "    return root\n\n"
            "vals = input().split()\n"
            "root = build(vals)\n"
            "print(max_depth(root))\n"
        ),
        "test_cases": [
            {"input": "3 9 20 null null 15 7", "expected_output": "3"},
            {"input": "1 null 2",              "expected_output": "2"},
            {"input": "1",                     "expected_output": "1"},
        ],
        "xp_reward": 175, "estimated_minutes": 25, "difficulty_multiplier": 3.0,
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample skills and quests for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing skills and quests before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Quest.objects.all().delete()
            SkillPrerequisite.objects.all().delete()
            Skill.objects.all().delete()

        # ── Seed skills ──────────────────────────────────────────────────────
        self.stdout.write("Seeding skills...")
        skill_map = {}
        for title, desc, cat, diff, xp in SKILLS:
            skill, created = Skill.objects.get_or_create(
                title=title,
                defaults={"description": desc, "category": cat, "difficulty": diff, "xp_required_to_unlock": xp},
            )
            skill_map[title] = skill
            status = "created" if created else "exists"
            self.stdout.write(f"  {status}: {title}")

        # ── Seed quests ──────────────────────────────────────────────────────
        self.stdout.write("\nSeeding quests...")
        created_count = 0
        skipped_count = 0
        for q in QUESTS:
            skill = skill_map.get(q["skill"])
            if not skill:
                self.stdout.write(self.style.WARNING(f"  Skipped (no skill): {q['title']}"))
                skipped_count += 1
                continue

            _, created = Quest.objects.get_or_create(
                title=q["title"],
                skill=skill,
                defaults={
                    "type":                 q["type"],
                    "description":          q["description"],
                    "starter_code":         q["starter_code"],
                    "test_cases":           q["test_cases"],
                    "xp_reward":            q["xp_reward"],
                    "estimated_minutes":    q["estimated_minutes"],
                    "difficulty_multiplier": q["difficulty_multiplier"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  created: [{q['type']}] {q['title']} (+{q['xp_reward']} XP)")
            else:
                skipped_count += 1
                self.stdout.write(f"  exists:  {q['title']}")

        # ── Summary ──────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Done — {created_count} quests created, {skipped_count} skipped"
        ))
        self.stdout.write(f"   Total quests in DB: {Quest.objects.count()}")
        self.stdout.write(f"   Total skills in DB: {Skill.objects.count()}")
