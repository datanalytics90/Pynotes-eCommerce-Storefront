from django import template

register = template.Library()

# Each book gets a consistent accent colour and a short cover label, keyed by SKU so it
# survives renames. Deliberately text/colour only (no language logos) to avoid trademark
# lookalikes — the brand's own "</>" motif (from static/css/style.css) supplies the icon.
_SKU_STYLES = {
    "PYN-PY": ("#2563eb", "PY"),
    "PYN-JAVA": ("#b91c1c", "JAVA"),
    "PYN-C": ("#0f766e", "C"),
    "PYN-CPP": ("#1e40af", "C++"),
    "PYN-DSA-PY": ("#7c3aed", "DSA·PY"),
    "PYN-DSA-JAVA": ("#7c3aed", "DSA·JAVA"),
    "PYN-DBMS": ("#b45309", "DBMS"),
    "PYN-OS": ("#0e7490", "OS"),
    "PYN-CN": ("#4338ca", "CN"),
    "PYN-OOPS": ("#be185d", "OOP"),
    "PYN-SQL": ("#15803d", "SQL"),
    "PYN-GIT": ("#334155", "GIT"),
    "PYN-APT": ("#c2410c", "APT"),
}
_DEFAULT_STYLE = ("#12A5B0", "PN")
_BUNDLE_STYLE = ("#D97706", "BUNDLE")


@register.filter
def book_accent(product):
    if product.is_bundle:
        return _BUNDLE_STYLE[0]
    return _SKU_STYLES.get(product.sku, _DEFAULT_STYLE)[0]


@register.filter
def book_code(product):
    if product.is_bundle:
        return _BUNDLE_STYLE[1]
    return _SKU_STYLES.get(product.sku, _DEFAULT_STYLE)[1]
