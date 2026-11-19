"""Narrow identity-label aliases; values still require exact document evidence."""

def canonical_identity(document, label):
    normalized=' '.join(label.strip().lower().split())
    aliases={('PO','supplier name'):'Supplier',('MTR','supplier name'):'Supplier',('PO','specification'):'Required Specification',('PO','material specification'):'Required Specification'}
    return aliases.get((document,normalized),label)


import re

def canonical_measurement(label):
    # Accept only known names; source quote, unit and cross-check still apply.
    text = ' '.join(label.strip().split())
    text = re.sub(r'\s+result$', '', text, flags=re.I)
    match = re.fullmatch(r'(?:element\s+)?(al|v|fe|o|c|n|h)', text, re.I)
    if match:
        return {'al':'Al','v':'V','fe':'Fe','o':'O','c':'C','n':'N','h':'H'}[match.group(1).lower()]
    names = ('Ultimate Tensile Strength', 'Yield Strength', 'Elongation')
    return next((name for name in names if text.casefold()==name.casefold()), label)
