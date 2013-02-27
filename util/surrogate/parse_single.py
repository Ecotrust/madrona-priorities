#!/usr/bin/python
import json
import collections

with open("single1.json", 'r') as fh:
    d = json.loads(fh.read())

def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def deslug(value): 
    words = value.split('-')
    words[0] = words[0].capitalize()
    return ' '.join(words)

with open('single_nocost.csv', 'w') as fh:
    d = [x for x in d if len(x['costs']) == 0]

    species = {
    }

    for x in d:
        cat, sp  = x['species'].split('---')
        target = x['target']
        if sp not in species.keys():
            temp = (deslug(sp), deslug(cat), [None] * 10) 
            species[sp] = list(flatten(temp))
            print list(flatten(temp))

        s = x['surrogate']
        val = 71 - s["species_missed"]

        species[sp][1 + int((target/10.0))] = val
     
    fh.write("species,category,10,20,30,40,50,60,70,80,90,100")
    for s,vals in species.items():
        fh.write("\n")
        fh.write(','.join([str(x) for x in vals]))
        print vals
        

with open('single_objscore_nocost.csv', 'w') as fh:
    d = [x for x in d if len(x['costs']) == 0]

    species = {
    }

    for x in d:
        cat, sp  = x['species'].split('---')
        target = x['target']
        if sp not in species.keys():
            temp = (deslug(sp), deslug(cat), [None] * 10) 
            species[sp] = list(flatten(temp))
            print list(flatten(temp))

        s = x['surrogate']
        val = s["objective_score"]

        species[sp][1 + int((target/10.0))] = val
     
    fh.write("species,category,10,20,30,40,50,60,70,80,90,100")
    for s,vals in species.items():
        fh.write("\n")
        fh.write(','.join([str(x) for x in vals]))
        print vals


