"""
Seed Skills — SkillTree AI
==============================
100 deterministic skills across 9 learning domains with prerequisite DAG edges.
All data is static — produces identical output on every seed run.
"""

from seeds.constants import DIFFICULTY_TIERS

# ---------------------------------------------------------------------------
# 100 Skills — (title, category, subcategory, difficulty, description)
# ---------------------------------------------------------------------------
# Ordering: skills within each category progress from beginner → expert.
# Index position determines the ordering_index field (0-99).

SKILLS = [
    # ── Data Structures (0-10) ───────────────────────────────────────────────
    ("Array Fundamentals", "ds", "Arrays & Strings", 1, "Master array traversal, indexing, and in-place manipulation techniques."),
    ("String Manipulation", "ds", "Arrays & Strings", 1, "Learn substring operations, pattern matching, and string encoding methods."),
    ("Two Pointer Technique", "ds", "Arrays & Strings", 2, "Apply the two-pointer pattern to solve array and string problems efficiently."),
    ("Singly Linked Lists", "ds", "Linked Lists", 2, "Build and traverse singly linked lists with insertion, deletion, and reversal."),
    ("Doubly Linked Lists", "ds", "Linked Lists", 3, "Implement doubly linked lists with bidirectional traversal and splice operations."),
    ("Stack Operations", "ds", "Stacks & Queues", 2, "Master LIFO operations for expression evaluation and backtracking."),
    ("Queue and Deque", "ds", "Stacks & Queues", 2, "Implement FIFO queues and double-ended queues for BFS and scheduling."),
    ("Binary Search Trees", "ds", "Trees & BSTs", 3, "Build balanced BSTs with insert, delete, search, and traversal operations."),
    ("Tree Traversals", "ds", "Trees & BSTs", 3, "Implement inorder, preorder, postorder, and level-order tree traversals."),
    ("Graph Representations", "ds", "Graphs", 4, "Model graphs using adjacency lists and matrices for real-world networks."),
    ("Graph Traversal Algorithms", "ds", "Graphs", 4, "Implement BFS and DFS for connected components, cycles, and pathfinding."),

    # ── Algorithms (11-21) ───────────────────────────────────────────────────
    ("Bubble and Selection Sort", "algorithms", "Sorting", 1, "Implement basic O(n²) sorting algorithms and understand their trade-offs."),
    ("Merge Sort", "algorithms", "Sorting", 2, "Master the divide-and-conquer merge sort with O(n log n) worst-case."),
    ("Quick Sort", "algorithms", "Sorting", 3, "Implement quicksort with pivot strategies and partition schemes."),
    ("Binary Search Basics", "algorithms", "Binary Search", 2, "Search sorted arrays in O(log n) using iterative and recursive approaches."),
    ("Advanced Binary Search", "algorithms", "Binary Search", 3, "Apply binary search to rotated arrays, 2D matrices, and answer spaces."),
    ("Recursive Thinking", "algorithms", "Recursion", 2, "Break problems into subproblems using recursion with base and recursive cases."),
    ("Backtracking", "algorithms", "Recursion", 3, "Solve constraint-satisfaction problems with systematic backtracking."),
    ("DP Memoization", "algorithms", "Dynamic Programming", 3, "Optimize recursive solutions with top-down memoization techniques."),
    ("DP Tabulation", "algorithms", "Dynamic Programming", 4, "Build bottom-up DP tables for optimal substructure problems."),
    ("Greedy Algorithms", "algorithms", "Greedy Techniques", 3, "Apply greedy choice property to interval scheduling and Huffman coding."),
    ("Advanced Greedy", "algorithms", "Greedy Techniques", 4, "Solve complex optimization problems using greedy strategies with proofs."),

    # ── AI / ML (22-32) ──────────────────────────────────────────────────────
    ("Supervised Learning Basics", "aiml", "ML Basics", 1, "Understand regression and classification with scikit-learn fundamentals."),
    ("Unsupervised Learning", "aiml", "ML Basics", 2, "Apply clustering and dimensionality reduction to discover data patterns."),
    ("Data Preprocessing", "aiml", "Feature Engineering", 2, "Clean, normalize, and transform raw data into ML-ready feature sets."),
    ("Feature Selection", "aiml", "Feature Engineering", 3, "Identify and select the most informative features to reduce dimensionality."),
    ("Cross-Validation", "aiml", "Model Evaluation", 2, "Evaluate model performance with k-fold cross-validation and stratification."),
    ("Metrics and Tuning", "aiml", "Model Evaluation", 3, "Master precision, recall, F1, AUC-ROC and hyperparameter optimization."),
    ("Feedforward Networks", "aiml", "Neural Networks", 3, "Build and train multi-layer perceptrons for classification tasks."),
    ("CNNs and RNNs", "aiml", "Neural Networks", 4, "Implement convolutional and recurrent architectures for vision and sequence data."),
    ("Prompt Engineering", "aiml", "LLM Prompting", 2, "Design effective prompts for large language models with few-shot examples."),
    ("RAG and Agents", "aiml", "LLM Prompting", 4, "Build retrieval-augmented generation pipelines and autonomous AI agents."),
    ("Transfer Learning", "aiml", "Neural Networks", 5, "Fine-tune pretrained models for domain-specific tasks with limited data."),

    # ── Web Development (33-43) ──────────────────────────────────────────────
    ("HTML Semantic Markup", "webdev", "HTML/CSS Foundations", 1, "Write accessible, semantic HTML5 with proper document structure."),
    ("CSS Layout Systems", "webdev", "HTML/CSS Foundations", 1, "Master Flexbox and CSS Grid for modern responsive page layouts."),
    ("CSS Animations", "webdev", "HTML/CSS Foundations", 2, "Create transitions and keyframe animations for polished UI interactions."),
    ("DOM Manipulation", "webdev", "JavaScript DOM", 2, "Select, create, and modify DOM elements with vanilla JavaScript."),
    ("Event Handling", "webdev", "JavaScript DOM", 2, "Handle user events with delegation, bubbling, and throttle patterns."),
    ("React Component Patterns", "webdev", "React Components", 3, "Build reusable functional components with hooks and composition."),
    ("React State Management", "webdev", "React Components", 3, "Manage complex state with useReducer, Context API, and external stores."),
    ("Django Models and Views", "webdev", "Django REST APIs", 3, "Build REST APIs with Django REST Framework serializers and viewsets."),
    ("API Authentication", "webdev", "Auth & Routing", 3, "Implement JWT authentication and permission classes in Django REST."),
    ("Frontend Routing", "webdev", "Auth & Routing", 2, "Configure client-side routing with React Router and protected routes."),
    ("Full-Stack Integration", "webdev", "Django REST APIs", 4, "Connect React frontends to Django backends with CORS and token refresh."),

    # ── Databases (44-54) ────────────────────────────────────────────────────
    ("SQL SELECT Queries", "databases", "SQL Queries", 1, "Write SELECT statements with WHERE, ORDER BY, and aggregate functions."),
    ("SQL JOINs", "databases", "SQL Queries", 2, "Combine tables with INNER, LEFT, RIGHT, and FULL OUTER joins."),
    ("Subqueries and CTEs", "databases", "SQL Queries", 3, "Write correlated subqueries and common table expressions for complex logic."),
    ("Normalization", "databases", "Schema Design", 2, "Design schemas in 1NF through 3NF to eliminate data redundancy."),
    ("Entity Relationship Modeling", "databases", "Schema Design", 2, "Model real-world domains with ER diagrams and cardinality constraints."),
    ("Index Strategies", "databases", "Indexes", 3, "Create B-tree, hash, and composite indexes for query optimization."),
    ("Covering Indexes", "databases", "Indexes", 4, "Design covering indexes to eliminate table lookups on hot queries."),
    ("ACID Transactions", "databases", "Transactions", 3, "Implement transactions with proper isolation levels and rollback handling."),
    ("Concurrency Control", "databases", "Transactions", 4, "Handle deadlocks, optimistic locking, and MVCC in concurrent workloads."),
    ("Query Plan Analysis", "databases", "PostgreSQL Tuning", 4, "Read EXPLAIN ANALYZE output and optimize slow PostgreSQL queries."),
    ("Connection Pooling", "databases", "PostgreSQL Tuning", 5, "Configure PgBouncer and connection pools for production PostgreSQL."),

    # ── System Design (55-65) ────────────────────────────────────────────────
    ("Horizontal vs Vertical Scaling", "sysdesign", "Scalability Basics", 1, "Compare scaling strategies and identify bottlenecks in system architecture."),
    ("Load Balancing", "sysdesign", "Scalability Basics", 2, "Distribute traffic across servers with round-robin and least-connections."),
    ("CDN and Edge Caching", "sysdesign", "Caching", 2, "Accelerate content delivery with CDN edge nodes and cache headers."),
    ("Application Caching", "sysdesign", "Caching", 3, "Implement Redis and Memcached caching with TTL and invalidation strategies."),
    ("Message Queue Fundamentals", "sysdesign", "Queues", 2, "Decouple services with RabbitMQ and Celery task queues."),
    ("Event-Driven Architecture", "sysdesign", "Queues", 4, "Design event-sourced systems with pub/sub and CQRS patterns."),
    ("WebSocket Basics", "sysdesign", "WebSockets", 3, "Build real-time features with WebSocket connections and Django Channels."),
    ("WebSocket Scaling", "sysdesign", "WebSockets", 4, "Scale WebSocket connections with Redis pub/sub and channel layers."),
    ("Logging and Metrics", "sysdesign", "Observability", 2, "Instrument applications with structured logging and Prometheus metrics."),
    ("Distributed Tracing", "sysdesign", "Observability", 4, "Trace requests across microservices with OpenTelemetry and Jaeger."),
    ("Rate Limiting", "sysdesign", "Scalability Basics", 3, "Protect APIs with token bucket and sliding window rate limiters."),

    # ── DevOps (66-76) ───────────────────────────────────────────────────────
    ("Git Branching Strategies", "devops", "Git Workflow", 1, "Use feature branches, rebasing, and pull request workflows effectively."),
    ("Git Advanced Operations", "devops", "Git Workflow", 2, "Master interactive rebase, cherry-pick, bisect, and reflog recovery."),
    ("Docker Containers", "devops", "Docker", 2, "Build, run, and manage Docker containers with optimized Dockerfiles."),
    ("Docker Compose", "devops", "Docker", 3, "Orchestrate multi-container applications with Docker Compose networks."),
    ("CI Pipeline Setup", "devops", "CI/CD", 2, "Configure GitHub Actions or GitLab CI pipelines for automated testing."),
    ("CD and Release Automation", "devops", "CI/CD", 3, "Automate deployments with blue-green, canary, and rolling release strategies."),
    ("Linux Command Line", "devops", "Linux CLI", 1, "Navigate the filesystem, manage processes, and write shell scripts."),
    ("Shell Scripting", "devops", "Linux CLI", 2, "Automate tasks with bash scripts, cron jobs, and environment management."),
    ("Cloud Deployments", "devops", "Deployments", 3, "Deploy applications to AWS, GCP, or Azure with infrastructure as code."),
    ("Kubernetes Basics", "devops", "Deployments", 4, "Orchestrate containers with Kubernetes pods, services, and deployments."),
    ("Infrastructure as Code", "devops", "Deployments", 5, "Manage cloud resources with Terraform modules and state management."),

    # ── Problem Solving (77-87) ──────────────────────────────────────────────
    ("Big-O Notation", "problemsolving", "Complexity Analysis", 1, "Analyze time and space complexity with Big-O, Big-Theta, and Big-Omega."),
    ("Amortized Analysis", "problemsolving", "Complexity Analysis", 3, "Calculate amortized costs for dynamic arrays and splay tree operations."),
    ("Sliding Window Pattern", "problemsolving", "Pattern Recognition", 2, "Apply the sliding window technique to substring and subarray problems."),
    ("Divide and Conquer Pattern", "problemsolving", "Pattern Recognition", 3, "Recognize and apply divide-and-conquer to sorting and search problems."),
    ("Systematic Debugging", "problemsolving", "Debugging", 2, "Use breakpoints, logging, and binary search to isolate bugs efficiently."),
    ("Memory Leak Detection", "problemsolving", "Debugging", 4, "Profile and fix memory leaks in Python and JavaScript applications."),
    ("Unit Testing Fundamentals", "problemsolving", "Test Design", 2, "Write focused unit tests with pytest and assertion best practices."),
    ("Test-Driven Development", "problemsolving", "Test Design", 3, "Practice red-green-refactor TDD cycles for robust code design."),
    ("Boundary Value Analysis", "problemsolving", "Edge Cases", 2, "Identify edge cases at boundaries of input domains and data types."),
    ("Error Handling Patterns", "problemsolving", "Edge Cases", 3, "Design robust error handling with custom exceptions and fallback logic."),
    ("Performance Profiling", "problemsolving", "Complexity Analysis", 4, "Profile Python code with cProfile and optimize hot paths."),

    # ── Product & UX (88-99) ─────────────────────────────────────────────────
    ("Navigation Design", "productux", "Information Architecture", 1, "Structure navigation hierarchies and sitemaps for intuitive wayfinding."),
    ("Content Hierarchy", "productux", "Information Architecture", 2, "Organize content with visual hierarchy, grouping, and progressive disclosure."),
    ("WCAG Compliance", "productux", "Accessibility", 2, "Implement WCAG 2.1 AA standards for color contrast, ARIA, and keyboard nav."),
    ("Screen Reader Optimization", "productux", "Accessibility", 3, "Optimize markup and ARIA labels for screen reader compatibility."),
    ("CSS Transitions", "productux", "Motion Design", 2, "Design meaningful micro-animations that enhance user feedback loops."),
    ("Animation Performance", "productux", "Motion Design", 3, "Optimize animations to run at 60fps using transform and opacity."),
    ("Mobile-First Layouts", "productux", "Responsive Layouts", 2, "Design mobile-first responsive layouts with fluid grids and breakpoints."),
    ("Adaptive Components", "productux", "Responsive Layouts", 3, "Build components that adapt layout, content, and behavior across devices."),
    ("User Journey Mapping", "productux", "User Flows", 2, "Map end-to-end user journeys to identify friction and drop-off points."),
    ("Conversion Optimization", "productux", "User Flows", 3, "Optimize signup, onboarding, and checkout flows with A/B testing."),
    ("Design System Foundations", "productux", "Information Architecture", 3, "Create reusable design tokens, component libraries, and style guides."),
    ("Usability Testing", "productux", "User Flows", 4, "Plan and conduct usability tests with task analysis and heuristic evaluation."),
]

# ---------------------------------------------------------------------------
# Prerequisite Edges — (from_skill_index, to_skill_index)
# Semantics: completing SKILLS[from] is required before SKILLS[to] unlocks.
# ---------------------------------------------------------------------------

PREREQUISITE_EDGES = [
    # Data Structures chain
    (0, 2),     # Array Fundamentals → Two Pointer Technique
    (1, 2),     # String Manipulation → Two Pointer Technique
    (0, 3),     # Array Fundamentals → Singly Linked Lists
    (3, 4),     # Singly Linked Lists → Doubly Linked Lists
    (0, 5),     # Array Fundamentals → Stack Operations
    (0, 6),     # Array Fundamentals → Queue and Deque
    (3, 7),     # Singly Linked Lists → Binary Search Trees
    (7, 8),     # Binary Search Trees → Tree Traversals
    (5, 9),     # Stack Operations → Graph Representations (DFS uses stacks)
    (6, 9),     # Queue and Deque → Graph Representations (BFS uses queues)
    (9, 10),    # Graph Representations → Graph Traversal Algorithms

    # Algorithms chain
    (0, 11),    # Array Fundamentals → Bubble and Selection Sort
    (11, 12),   # Bubble and Selection Sort → Merge Sort
    (12, 13),   # Merge Sort → Quick Sort
    (0, 14),    # Array Fundamentals → Binary Search Basics
    (14, 15),   # Binary Search Basics → Advanced Binary Search
    (11, 16),   # Bubble and Selection Sort → Recursive Thinking
    (16, 17),   # Recursive Thinking → Backtracking
    (16, 18),   # Recursive Thinking → DP Memoization
    (18, 19),   # DP Memoization → DP Tabulation
    (14, 20),   # Binary Search Basics → Greedy Algorithms
    (20, 21),   # Greedy Algorithms → Advanced Greedy

    # AI / ML chain
    (22, 23),   # Supervised Learning → Unsupervised Learning
    (22, 24),   # Supervised Learning → Data Preprocessing
    (24, 25),   # Data Preprocessing → Feature Selection
    (22, 26),   # Supervised Learning → Cross-Validation
    (26, 27),   # Cross-Validation → Metrics and Tuning
    (27, 28),   # Metrics and Tuning → Feedforward Networks
    (28, 29),   # Feedforward Networks → CNNs and RNNs
    (22, 30),   # Supervised Learning → Prompt Engineering
    (29, 31),   # CNNs and RNNs → RAG and Agents
    (29, 32),   # CNNs and RNNs → Transfer Learning

    # Web Development chain
    (33, 35),   # HTML Semantic Markup → CSS Animations
    (34, 35),   # CSS Layout Systems → CSS Animations
    (33, 36),   # HTML Semantic Markup → DOM Manipulation
    (36, 37),   # DOM Manipulation → Event Handling
    (37, 38),   # Event Handling → React Component Patterns
    (38, 39),   # React Component Patterns → React State Management
    (33, 40),   # HTML Semantic Markup → Django Models and Views
    (40, 41),   # Django Models and Views → API Authentication
    (37, 42),   # Event Handling → Frontend Routing
    (39, 43),   # React State Management → Full-Stack Integration
    (41, 43),   # API Authentication → Full-Stack Integration

    # Databases chain
    (44, 45),   # SQL SELECT → SQL JOINs
    (45, 46),   # SQL JOINs → Subqueries and CTEs
    (44, 47),   # SQL SELECT → Normalization
    (47, 48),   # Normalization → ER Modeling
    (45, 49),   # SQL JOINs → Index Strategies
    (49, 50),   # Index Strategies → Covering Indexes
    (46, 51),   # Subqueries and CTEs → ACID Transactions
    (51, 52),   # ACID Transactions → Concurrency Control
    (49, 53),   # Index Strategies → Query Plan Analysis
    (53, 54),   # Query Plan Analysis → Connection Pooling

    # System Design chain
    (55, 56),   # Horizontal vs Vertical → Load Balancing
    (55, 57),   # Horizontal vs Vertical → CDN and Edge Caching
    (57, 58),   # CDN and Edge Caching → Application Caching
    (55, 59),   # Horizontal vs Vertical → Message Queue Fundamentals
    (59, 60),   # Message Queue Fundamentals → Event-Driven Architecture
    (59, 61),   # Message Queue Fundamentals → WebSocket Basics
    (61, 62),   # WebSocket Basics → WebSocket Scaling
    (55, 63),   # Horizontal vs Vertical → Logging and Metrics
    (63, 64),   # Logging and Metrics → Distributed Tracing
    (56, 65),   # Load Balancing → Rate Limiting

    # DevOps chain
    (66, 67),   # Git Branching → Git Advanced
    (66, 70),   # Git Branching → CI Pipeline Setup
    (68, 69),   # Docker Containers → Docker Compose
    (70, 71),   # CI Pipeline → CD and Release Automation
    (72, 73),   # Linux CLI → Shell Scripting
    (69, 74),   # Docker Compose → Cloud Deployments
    (71, 74),   # CD and Release Automation → Cloud Deployments
    (74, 75),   # Cloud Deployments → Kubernetes Basics
    (75, 76),   # Kubernetes Basics → Infrastructure as Code

    # Problem Solving chain
    (77, 78),   # Big-O → Amortized Analysis
    (77, 79),   # Big-O → Sliding Window
    (79, 80),   # Sliding Window → Divide and Conquer
    (77, 81),   # Big-O → Systematic Debugging
    (81, 82),   # Systematic Debugging → Memory Leak Detection
    (77, 83),   # Big-O → Unit Testing Fundamentals
    (83, 84),   # Unit Testing → TDD
    (77, 85),   # Big-O → Boundary Value Analysis
    (85, 86),   # Boundary Value Analysis → Error Handling Patterns
    (78, 87),   # Amortized Analysis → Performance Profiling

    # Product & UX chain
    (88, 89),   # Navigation Design → Content Hierarchy
    (88, 90),   # Navigation Design → WCAG Compliance
    (90, 91),   # WCAG Compliance → Screen Reader Optimization
    (88, 92),   # Navigation Design → CSS Transitions
    (92, 93),   # CSS Transitions → Animation Performance
    (88, 94),   # Navigation Design → Mobile-First Layouts
    (94, 95),   # Mobile-First Layouts → Adaptive Components
    (88, 96),   # Navigation Design → User Journey Mapping
    (96, 97),   # User Journey Mapping → Conversion Optimization
    (89, 98),   # Content Hierarchy → Design System Foundations
    (97, 99),   # Conversion Optimization → Usability Testing

    # Cross-category edges
    (0, 22),    # Array Fundamentals → Supervised Learning (data foundations)
    (44, 40),   # SQL SELECT → Django Models (DB before ORM)
    (68, 40),   # Docker Containers → Django Models (containerized dev)
    (77, 16),   # Big-O → Recursive Thinking (complexity before recursion)
    (83, 81),   # Unit Testing → Systematic Debugging (testing informs debugging)
]
