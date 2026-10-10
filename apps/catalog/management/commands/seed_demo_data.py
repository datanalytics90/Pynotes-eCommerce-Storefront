import io
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from apps.catalog.models import Category, Coupon, Product, ProductImage

CATEGORIES = [
    ("Ebooks", "#2563eb"),
    ("Video Courses", "#7c3aed"),
    ("Notebooks & Templates", "#059669"),
    ("Dev Merch", "#d97706"),
    ("Stickers & Accessories", "#dc2626"),
]

PRODUCTS = [
    {
        "category": "Ebooks",
        "name": "Python for Data Analysis — 2026 Edition",
        "price": Decimal("24.99"),
        "compare_at_price": Decimal("34.99"),
        "is_digital": True,
        "short_description": "A practical, example-driven guide to pandas, NumPy and data wrangling.",
        "description": (
            "This ebook walks through real-world data analysis workflows in Python: cleaning messy "
            "datasets, reshaping with pandas, visualizing with matplotlib/seaborn, and exporting "
            "reproducible reports. Includes downloadable Jupyter notebooks for every chapter."
        ),
        "featured": True,
    },
    {
        "category": "Ebooks",
        "name": "Machine Learning Fundamentals Handbook",
        "price": Decimal("29.99"),
        "is_digital": True,
        "short_description": "From linear regression to gradient boosting, explained without the fluff.",
        "description": "A concise reference covering supervised and unsupervised learning, model "
        "evaluation, feature engineering and deployment basics, with scikit-learn code throughout.",
    },
    {
        "category": "Video Courses",
        "name": "Complete Python Bootcamp: Zero to Data Scientist",
        "price": Decimal("79.00"),
        "compare_at_price": Decimal("149.00"),
        "is_digital": True,
        "short_description": "40+ hours of video, projects and quizzes covering Python and core data science tools.",
        "description": "A full bootcamp-style course: Python fundamentals, OOP, pandas/NumPy, "
        "visualization, SQL, and an intro to machine learning — with 6 capstone projects and "
        "lifetime access.",
        "featured": True,
    },
    {
        "category": "Video Courses",
        "name": "FastAPI & Django Masterclass",
        "price": Decimal("59.00"),
        "is_digital": True,
        "short_description": "Build and deploy production-grade APIs and web apps with Python.",
        "description": "Learn to design REST APIs with FastAPI and Django REST Framework, add "
        "authentication, connect PostgreSQL, write tests, and deploy with Docker.",
    },
    {
        "category": "Notebooks & Templates",
        "name": "EDA Starter Notebook Pack (20 notebooks)",
        "price": Decimal("14.99"),
        "is_digital": True,
        "short_description": "Ready-to-use exploratory data analysis notebooks for common dataset types.",
        "description": "20 battle-tested Jupyter notebook templates covering univariate/bivariate "
        "analysis, missing data handling, outlier detection and automated profiling reports.",
    },
    {
        "category": "Notebooks & Templates",
        "name": "SQL + Pandas Cheat Sheet Bundle",
        "price": Decimal("9.99"),
        "is_digital": True,
        "short_description": "Printable PDF cheat sheets mapping SQL queries to pandas equivalents.",
        "description": "A handy reference bundle for analysts switching between SQL and pandas, "
        "covering joins, aggregations, window functions and more.",
    },
    {
        "category": "Dev Merch",
        "name": "Pynotes 'import this' Hoodie",
        "price": Decimal("44.00"),
        "is_digital": False,
        "stock": 60,
        "short_description": "Heavyweight cotton hoodie with The Zen of Python on the back.",
        "description": "350gsm brushed-fleece hoodie, unisex fit, with an embroidered logo on the "
        "chest and a screen-printed Zen of Python on the back. Machine washable.",
        "featured": True,
    },
    {
        "category": "Dev Merch",
        "name": "Pynotes Classic Logo T-Shirt",
        "price": Decimal("22.00"),
        "is_digital": False,
        "stock": 120,
        "short_description": "Soft 100% combed cotton tee with the Pynotes logo.",
        "description": "A breathable, pre-shrunk cotton t-shirt available in multiple sizes, "
        "printed with eco-friendly water-based inks.",
    },
    {
        "category": "Stickers & Accessories",
        "name": "Python Libraries Sticker Pack (12-pack)",
        "price": Decimal("8.50"),
        "is_digital": False,
        "stock": 300,
        "short_description": "Die-cut vinyl stickers for pandas, NumPy, Django, FastAPI and more.",
        "description": "Weatherproof, laptop-ready vinyl stickers featuring 12 of the most popular "
        "Python and data tools — perfect for laptops, water bottles and notebooks.",
        "featured": True,
    },
    {
        "category": "Stickers & Accessories",
        "name": "Pynotes Enamel Pin Set (3-pack)",
        "price": Decimal("12.00"),
        "is_digital": False,
        "stock": 150,
        "short_description": "Hard enamel pins with a Python logo, a terminal icon, and the Pynotes mark.",
        "description": "A collectible set of three gold-plated hard enamel pins with butterfly "
        "clutch backs, packaged in a branded gift card.",
    },
]


def make_placeholder_image(text, color):
    img = Image.new("RGB", (800, 800), color=color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("Arial.ttf", 42)
    except OSError:
        font = ImageFont.load_default()

    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) > 18:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)

    total_height = len(lines) * 55
    y = (800 - total_height) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((800 - w) / 2, y), line, fill="white", font=font)
        y += 55

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = "Seeds the catalog with demo categories, products, images and a sample coupon."

    def handle(self, *args, **options):
        category_objs = {}
        for index, (name, color) in enumerate(CATEGORIES):
            category, _ = Category.objects.get_or_create(
                name=name, defaults={"order": index, "description": f"{name} for Python & data practitioners."}
            )
            category_objs[name] = (category, color)

        created_count = 0
        for i, data in enumerate(PRODUCTS):
            category, color = category_objs[data["category"]]
            product, created = Product.objects.get_or_create(
                sku=f"PYN-{1000 + i}",
                defaults={
                    "category": category,
                    "name": data["name"],
                    "description": data["description"],
                    "short_description": data["short_description"],
                    "price": data["price"],
                    "compare_at_price": data.get("compare_at_price"),
                    "stock": data.get("stock", 0),
                    "is_digital": data["is_digital"],
                    "is_featured": data.get("featured", False),
                },
            )
            if created:
                created_count += 1
                image_file = make_placeholder_image(data["name"], color)
                image = ProductImage(product=product, is_primary=True)
                image.image.save(f"{product.slug}.jpg", image_file, save=True)

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

        self.stdout.write(self.style.SUCCESS(f"Seed complete: {created_count} new products created."))
