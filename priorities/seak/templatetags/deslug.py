from django import template

register = template.Library()

@register.filter 
def deslug(value): 
    words = value.split('-')
    words[0] = words[0].capitalize()
    return ' '.join(words)
