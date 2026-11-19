from decimal import Decimal

def convert(value, source, target):
    x = Decimal(str(value))
    if source == target: return x
    if (source, target) == ('ksi', 'MPa'): return x * Decimal('6.894757293168')
    raise ValueError(f'Unsupported unit: {source} -> {target}')

def evaluate(spec, values, identifiers, expected_identifiers):
    findings = []
    for rule in spec['rules']:
        name = rule['field']
        measurement = values.get(name)
        if measurement is None:
            findings.append((name, 'MISSING', None, rule['unit']))
            continue
        try: value = convert(measurement['value'], measurement['unit'], rule['unit'])
        except (ValueError, TypeError):
            findings.append((name, 'UNCLEAR_UNIT', measurement['value'], measurement['unit']))
            continue
        if ('min' in rule and (value < Decimal(str(rule['min'])) if rule['min_inclusive'] else value <= Decimal(str(rule['min'])))) or ('max' in rule and (value > Decimal(str(rule['max'])) if rule['max_inclusive'] else value >= Decimal(str(rule['max'])))):
            findings.append((name, 'OUT_OF_RANGE', measurement['value'], measurement['unit']))
    for key, expected in expected_identifiers.items():
        actual = identifiers.get(key)
        if actual is None: findings.append((key, 'MISSING', None, ''))
        elif actual != expected: findings.append((key, 'MISMATCH', actual, ''))
    verdict = 'NONCONFORMING' if any(f[1] in ('OUT_OF_RANGE', 'MISMATCH') for f in findings) else ('REVIEW_REQUIRED' if findings else 'CONFORMING')
    return verdict, findings
