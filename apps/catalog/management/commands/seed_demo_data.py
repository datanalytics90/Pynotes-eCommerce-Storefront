from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalog.models import BundleItem, Category, Coupon, Product
from apps.core.models import FAQ, AnnouncementMessage, LegalPage, SiteSettings, Testimonial

BOOKS = [
    {
        "sku": "PYN-PY",
        "category": "Python",
        "name": "Python Simplified Handwritten Notes",
        "price": Decimal("499"),
        "compare": Decimal("799"),
        "short": "Clear, structured coding notes designed around the learner's desk.",
        "desc": "A complete handwritten-style guide to Python: syntax, data structures, OOP, "
        "file handling and a few real mini-projects — laid out the way a good student writes it, "
        "with margin notes and diagrams textbooks leave out.",
        "featured": True,
    },
    {
        "sku": "PYN-JAVA",
        "category": "Java",
        "name": "Java Simplified Handwritten Notes",
        "price": Decimal("499"),
        "compare": Decimal("799"),
        "short": "Core Java concepts, written out clearly with worked examples.",
        "desc": "Covers Java fundamentals, OOP, collections, exception handling and a short "
        "intro to multithreading, with handwritten-style diagrams throughout.",
        "featured": True,
    },
    {
        "sku": "PYN-C",
        "category": "C",
        "name": "C Programming Handwritten Notes",
        "price": Decimal("399"),
        "compare": Decimal("799"),
        "short": "Pointers, memory and the fundamentals, explained without the jargon.",
        "desc": "From variables and loops to pointers, structures and file I/O — the notes "
        "that make C finally click, with plenty of traced-through examples.",
    },
    {
        "sku": "PYN-CPP",
        "category": "C++",
        "name": "C++ Simplified Handwritten Notes",
        "price": Decimal("499"),
        "compare": Decimal("799"),
        "short": "OOP in C++ with STL essentials, clearly diagrammed.",
        "desc": "Classes, inheritance, polymorphism, templates and a practical tour of the STL "
        "— written the way a senior would explain it to a junior.",
    },
    {
        "sku": "PYN-DSA-PY",
        "category": "DSA with Python",
        "name": "DSA with Python Handwritten Notes",
        "price": Decimal("499"),
        "compare": Decimal("799"),
        "short": "Arrays to graphs, implemented and explained in Python.",
        "desc": "Core data structures and algorithms — arrays, linked lists, stacks, queues, "
        "trees, graphs, sorting and Big-O — each with Python implementations and complexity notes.",
        "featured": True,
    },
    {
        "sku": "PYN-DSA-JAVA",
        "category": "DSA with Java",
        "name": "DSA with Java Handwritten Notes",
        "price": Decimal("499"),
        "compare": Decimal("799"),
        "short": "The same DSA fundamentals, implemented in Java.",
        "desc": "Core data structures and algorithms for Java learners — arrays through graphs, "
        "sorting, searching and complexity analysis, with Java code throughout.",
    },
    {
        "sku": "PYN-DBMS",
        "category": "Core CS",
        "name": "DBMS Handwritten Notes",
        "price": Decimal("449"),
        "compare": Decimal("799"),
        "short": "Database fundamentals: normalization, SQL, transactions and keys.",
        "desc": "ER modelling, normal forms, SQL queries, joins, transactions and indexing — "
        "the DBMS fundamentals most interviews and coursework actually test.",
    },
    {
        "sku": "PYN-OS",
        "category": "Core CS",
        "name": "Operating Systems Handwritten Notes",
        "price": Decimal("449"),
        "compare": Decimal("799"),
        "short": "Processes, scheduling, memory and deadlocks, clearly diagrammed.",
        "desc": "Process/thread basics, CPU scheduling algorithms, memory management, "
        "paging, and deadlock handling, with diagrams for every tricky concept.",
    },
    {
        "sku": "PYN-CN",
        "category": "Core CS",
        "name": "Computer Networks Handwritten Notes",
        "price": Decimal("449"),
        "compare": Decimal("799"),
        "short": "OSI/TCP-IP layers, routing and protocols, simplified.",
        "desc": "The OSI and TCP/IP models, addressing, routing basics, and the protocols "
        "(HTTP, DNS, TCP, UDP) that come up again and again in interviews.",
    },
    {
        "sku": "PYN-OOPS",
        "category": "Core CS",
        "name": "OOP Concepts Handwritten Notes",
        "price": Decimal("349"),
        "compare": Decimal("599"),
        "short": "Encapsulation, inheritance, polymorphism — language-agnostic.",
        "desc": "The four pillars of OOP explained with language-agnostic examples, plus common "
        "design pitfalls and a short intro to SOLID principles.",
    },
    {
        "sku": "PYN-SQL",
        "category": "Core CS",
        "name": "SQL Handwritten Notes",
        "price": Decimal("349"),
        "compare": Decimal("599"),
        "short": "Queries, joins and window functions, worked through by hand.",
        "desc": "SELECT to window functions: filtering, joins, aggregation, subqueries and the "
        "query patterns that show up most often in data and backend interviews.",
    },
    {
        "sku": "PYN-GIT",
        "category": "Core CS",
        "name": "Git & GitHub Handwritten Notes",
        "price": Decimal("299"),
        "compare": Decimal("499"),
        "short": "Branching, merging and pull requests, explained simply.",
        "desc": "A practical walkthrough of Git fundamentals and the GitHub workflow most teams "
        "actually use day to day — branches, merges, rebases and pull requests.",
    },
    {
        "sku": "PYN-APT",
        "category": "Core CS",
        "name": "Aptitude & Interview Prep Notes",
        "price": Decimal("399"),
        "compare": Decimal("599"),
        "short": "Quant, logical reasoning and common interview questions.",
        "desc": "A focused set of handwritten notes covering quantitative aptitude, logical "
        "reasoning and the most frequently asked technical interview questions.",
    },
]

BUNDLES = [
    {
        "sku": "PYN-BND-PYJAVA",
        "name": "Python + Java Bundle",
        "price": Decimal("899"),
        "compare": Decimal("998"),
        "books": ["PYN-PY", "PYN-JAVA"],
    },
    {
        "sku": "PYN-BND-CCPPY",
        "name": "C + C++ + Python Bundle",
        "price": Decimal("1199"),
        "compare": Decimal("1397"),
        "books": ["PYN-C", "PYN-CPP", "PYN-PY"],
    },
    {
        "sku": "PYN-BND-CPPJAVAPY",
        "name": "C++ + Java + Python Bundle",
        "price": Decimal("1299"),
        "compare": Decimal("1497"),
        "books": ["PYN-CPP", "PYN-JAVA", "PYN-PY"],
    },
    {
        "sku": "PYN-BND-ALL4",
        "name": "All Four Languages Bundle",
        "price": Decimal("1599"),
        "compare": Decimal("1996"),
        "books": ["PYN-C", "PYN-CPP", "PYN-JAVA", "PYN-PY"],
    },
]

FAQS = [
    (
        "ordering", "Do you sell digital/PDF notes?",
        "No — PyNotes are printed, physical books only. We don't sell downloads.",
    ),
    (
        "ordering", "Can I buy a bundle of subjects?",
        "Yes, several Smart Bundles are available at a lower combined price than buying each book separately.",
    ),
    (
        "payments", "What payment methods do you accept?",
        "Prepaid via UPI, cards and wallets through Razorpay, or Cash on Delivery with a small COD fee.",
    ),
    (
        "payments", "Is there a discount for prepaid orders?",
        "Yes, prepaid orders get an automatic discount shown at checkout.",
    ),
    (
        "shipping", "How long does delivery take?",
        "Orders are processed in 1–2 business days and delivered in 3–7 business days across India.",
    ),
    ("shipping", "Do you ship across India?", "Yes, we ship pan-India with tracked courier delivery."),
    (
        "returns", "What if my book arrives damaged?",
        "Report it within 48 hours of delivery with photos via your account's 'Report an issue' page.",
    ),
    ("returns", "Can I cancel my order?", "Orders can be cancelled any time before they're dispatched."),
    (
        "general", "Do you provide GST invoices?",
        "Yes, a GST invoice is generated for every order and can be downloaded from your order page.",
    ),
]

LEGAL_PAGES = {
    "privacy": (
        "Privacy Policy",
        "We collect only the information needed to process your order: name, shipping address, "
        "phone number and email. We never sell your data. Payment details are handled directly by "
        "Razorpay and never touch our servers. Contact us any time to request deletion of your data.",
    ),
    "terms": (
        "Terms & Conditions",
        "By ordering from PyNotes you agree to pay the listed price (plus any COD fee or prepaid "
        "discount applied at checkout) for printed books shipped to the address you provide. "
        "Prices and availability are subject to change without notice.",
    ),
    "shipping": (
        "Shipping Policy",
        "Orders are processed within 1-2 business days and typically delivered within 3-7 business "
        "days anywhere in India via our courier partner. You'll receive a tracking link by email once "
        "your order ships.",
    ),
    "refund": (
        "Refund & Cancellation Policy",
        "Orders can be cancelled free of charge any time before they are dispatched. Once shipped, "
        "damaged or incorrect items must be reported within 48 hours of delivery with photos, after "
        "which we'll arrange a replacement or refund.",
    ),
}


class Command(BaseCommand):
    help = "Seeds categories, books, bundles, FAQs, legal pages, testimonials and site settings."

    def handle(self, *args, **options):
        settings_obj = SiteSettings.load()
        if not settings_obj.whatsapp_number:
            settings_obj.whatsapp_number = "+91 90000 00000"
            settings_obj.gstin = ""
            settings_obj.legal_business_name = "PyNotes"
            settings_obj.save()

        for text in [
            "Printed coding notes made to learn, write and grow",
            f"{settings_obj.prepaid_discount_percent}% off on every prepaid order",
            "Cash on Delivery available across India",
        ]:
            AnnouncementMessage.objects.get_or_create(text=text)

        language_categories = [("Python", "python"), ("Java", "java"), ("C", "c"), ("C++", "cpp")]
        category_objs = {}
        for index, (name, slug) in enumerate(language_categories):
            cat, _ = Category.objects.get_or_create(name=name, defaults={"order": index, "slug": slug})
            category_objs[name] = cat

        dsa_parent, _ = Category.objects.get_or_create(name="DSA", defaults={"order": 10})
        category_objs["DSA with Python"], _ = Category.objects.get_or_create(
            name="DSA with Python", defaults={"order": 11, "parent": dsa_parent}
        )
        category_objs["DSA with Java"], _ = Category.objects.get_or_create(
            name="DSA with Java", defaults={"order": 12, "parent": dsa_parent}
        )
        category_objs["Core CS"], _ = Category.objects.get_or_create(name="Core CS", defaults={"order": 20})
        bundles_category, _ = Category.objects.get_or_create(name="Bundles", defaults={"order": 30})

        created_books = 0
        for data in BOOKS:
            category = category_objs[data["category"]]
            _, created = Product.objects.get_or_create(
                sku=data["sku"],
                defaults={
                    "category": category,
                    "name": data["name"],
                    "description": data["desc"],
                    "short_description": data["short"],
                    "price": data["price"],
                    "compare_at_price": data["compare"],
                    "stock": 100,
                    "hsn_code": "4901",
                    "is_bundle": False,
                    "is_featured": data.get("featured", False),
                },
            )
            created_books += created

        created_bundles = 0
        for data in BUNDLES:
            bundle, created = Product.objects.get_or_create(
                sku=data["sku"],
                defaults={
                    "category": bundles_category,
                    "name": data["name"],
                    "description": f"Save by buying {len(data['books'])} subjects together — "
                    "stock for this bundle always follows the books inside it.",
                    "short_description": "A lower combined price for multiple subjects.",
                    "price": data["price"],
                    "compare_at_price": data["compare"],
                    "stock": 0,
                    "hsn_code": "4901",
                    "is_bundle": True,
                },
            )
            created_bundles += created
            if created:
                for sku in data["books"]:
                    book = Product.objects.get(sku=sku)
                    BundleItem.objects.get_or_create(bundle=bundle, book=book, defaults={"quantity": 1})

        for group, question, answer in FAQS:
            FAQ.objects.get_or_create(question=question, defaults={"answer": answer, "group": group})

        for slug, (title, body) in LEGAL_PAGES.items():
            LegalPage.objects.get_or_create(slug=slug, defaults={"title": title, "body": body})

        Testimonial.objects.get_or_create(
            author_name="Ananya R.",
            defaults={
                "quote": "The Python notes made recursion finally click for me — way clearer than my college textbook.",
                "platform": "Google",
            },
        )
        Testimonial.objects.get_or_create(
            author_name="Rohit K.",
            defaults={
                "quote": "Ordered the DSA + Python bundle before placements. Clean handwriting, easy to follow.",
                "platform": "Instagram",
            },
        )
        Testimonial.objects.get_or_create(
            author_name="Sneha M.",
            defaults={
                "quote": "COD was smooth and the book arrived in great condition within 4 days.",
                "platform": "Email",
            },
        )

        Coupon.objects.get_or_create(
            code="WELCOME10",
            defaults={
                "discount_percent": 10,
                "active": True,
                "valid_from": timezone.now() - timezone.timedelta(days=1),
                "valid_to": timezone.now() + timezone.timedelta(days=365),
                "usage_limit": 0,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(f"Seed complete: {created_books} books, {created_bundles} bundles created.")
        )
