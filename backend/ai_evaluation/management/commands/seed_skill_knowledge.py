"""
Management command to seed skill knowledge into ChromaDB.
Usage: python manage.py seed_skill_knowledge
       python manage.py seed_skill_knowledge --reset  (clear and re-seed)
"""

from django.core.management.base import BaseCommand
from skills.models import Skill
from core.chroma_client import chroma_client


# Best practices for each skill category
BEST_PRACTICES = {
    "algorithms": """
- Analyze time and space complexity before implementing
- Consider edge cases (empty input, single element, duplicates)
- Use appropriate data structures for the problem
- Write clean, readable code with meaningful variable names
- Add comments for complex logic
- Test with various input sizes
""",
    "ds": """
- Understand the data structure's properties and operations
- Know when to use each data structure (array vs linked list, stack vs queue)
- Consider memory allocation and deallocation
- Implement proper error handling
- Use iterative solutions when possible to avoid stack overflow
- Visualize the data structure to understand operations
""",
    "systems": """
- Write modular, maintainable code
- Handle errors gracefully
- Consider concurrency and thread safety
- Optimize for performance where needed
- Document system architecture and design decisions
- Follow SOLID principles
""",
    "webdev": """
- Write semantic, accessible HTML
- Use modern CSS features (flexbox, grid, custom properties)
- Follow responsive design principles
- Optimize for performance (lazy loading, code splitting)
- Ensure cross-browser compatibility
- Implement proper error handling and validation
- Follow REST API best practices
""",
    "aiml": """
- Understand the problem and data before choosing algorithms
- Preprocess and clean data properly
- Split data into train/validation/test sets
- Use appropriate evaluation metrics
- Avoid overfitting with regularization and cross-validation
- Document model architecture and hyperparameters
- Consider ethical implications and bias
"""
}


class Command(BaseCommand):
    help = "Seed ChromaDB with skill knowledge for RAG-based evaluation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset ChromaDB collections before seeding",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Resetting ChromaDB collections...")
            chroma_client.reset_all_collections()
            self.stdout.write(self.style.SUCCESS("✓ Collections reset"))

        self.stdout.write("Seeding skill knowledge to ChromaDB...")
        
        skills = Skill.objects.all()
        if not skills.exists():
            self.stdout.write(self.style.WARNING(
                "No skills found in database. Run 'python manage.py seed_quests' first."
            ))
            return

        seeded_count = 0
        for skill in skills:
            # Get best practices for category
            best_practices = BEST_PRACTICES.get(skill.category, "")
            
            # Upsert to ChromaDB
            chroma_client.upsert_skill_knowledge(
                skill_id=skill.id,
                title=skill.title,
                description=skill.description,
                category=skill.category,
                difficulty=skill.difficulty,
                best_practices=best_practices
            )
            
            seeded_count += 1
            self.stdout.write(
                f"  ✓ Seeded: {skill.title} ({skill.category}, difficulty {skill.difficulty})"
            )

        # Show stats
        stats = chroma_client.get_collection_stats()
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Done — {seeded_count} skills seeded to ChromaDB"
        ))
        self.stdout.write("\nCollection Stats:")
        self.stdout.write(f"  • skill_knowledge: {stats['skill_knowledge']} documents")
        self.stdout.write(f"  • code_patterns: {stats['code_patterns']} documents")
        self.stdout.write(f"  • ai_code_samples: {stats['ai_code_samples']} documents")
