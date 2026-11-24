# Automatismes de Première — vérification des 25 exercices

Code de vérification de la vidéo Matheux Malin « Automatismes maths Première : 25 exercices corrigés sans
calculatrice ». Vidéo : https://youtu.be/V2SWrojJ1s4

Les exercices sont **originaux**, écrits pour la chaîne. Ils couvrent les cinq blocs de la liste « Automatismes »
du programme de spécialité mathématiques de Première (arrêté du 26 février 2026, BO n° 14 du 2 avril 2026) :
évolutions et variations, calcul numérique et algébrique, fonctions et représentations, statistiques,
probabilités. Aucun énoncé d'examen n'est repris.

## Fichiers

| Fichier | Rôle |
|---|---|
| `verif.py` | Énoncés des 25 exercices, calcul exact de chaque réponse (`fractions`, `sympy`) et des erreurs fréquentes (le « piège » de chaque exercice, avec le résultat faux qu'il donne) |
| `test_verif.py` | Tests GIVEN / WHEN / THEN : chaque réponse est **recalculée par une autre méthode** (remplacement de x, comptage sur 1 000 personnes, opération inverse…) |
| `preuves/exercices.json` | Sortie de `verif.py` : ce que la vidéo affiche et dit (énoncé, réponse, pièges, et **chaque étape intermédiaire** prononcée dans la voix off) |

## Lancer

Python 3.10 ou plus, et `sympy` :

```
pip install sympy
python verif.py              # écrit preuves/exercices.json et affiche les 25 réponses
python -m unittest -v        # lance les tests
```

## Pourquoi deux calculs pour chaque réponse

`verif.py` calcule la réponse « comme dans le cours » ; `test_verif.py` la vérifie autrement (par exemple :
pour une valeur initiale avant baisse, on rebaisse le résultat et on doit retomber sur le prix de l'énoncé). Si
les deux méthodes ne donnent pas la même chose, le test échoue et rien n'est affiché dans la vidéo.

## Avertissement

Ces exercices aident à réviser ; ils ne remplacent pas les cours de ton professeur. Les programmes officiels
(ministère de l'Éducation nationale, Eduscol) restent la référence.
