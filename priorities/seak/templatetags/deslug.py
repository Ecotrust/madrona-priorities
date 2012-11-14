from django import template

register = template.Library()

def make_acronym(w):
    acronyms = [
        'BLM',
    ]
    if w.upper() in acronyms:
        return w.upper()
    else:
        return w

@register.filter 
def deslug(value): 
    words = value.split('-')
    words[0] = words[0].capitalize()
    words = [make_acronym(w) for w in words]
    return ' '.join(words)
