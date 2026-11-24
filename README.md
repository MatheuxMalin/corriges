# Matheux Malin — code de vérification des corrigés

Chaque vidéo de la chaîne YouTube [Matheux Malin](https://www.youtube.com/@MatheuxMalin) affiche des résultats
**vérifiés par un programme Python** avant d'être montrés. Ce dépôt publie ce code : un dossier par vidéo.

## Contenu d'un dossier

| Fichier | Rôle |
|---|---|
| `verif.py` | Calcule chaque réponse de façon exacte (`fractions`, `sympy`) |
| `test_verif.py` | Tests (GIVEN / WHEN / THEN) : bonnes réponses, et origine de chaque mauvaise réponse de QCM |
| `preuves/` | Résultats produits par le programme, lus par les cartes de la vidéo |
| `README.md` | Lien vers la vidéo et vers l'énoncé officiel |

Les énoncés ne sont pas recopiés : chaque question est référencée (session, numéro) avec un lien vers la source
officielle.

## Lancer la vérification

```
pip install sympy pytest
cd <dossier-de-la-video>
python verif.py
pytest
```

## Avertissement

Ces corrigés aident à réviser ; ils ne remplacent pas les cours de ton professeur. Les programmes et sujets
officiels (ministère de l'Éducation nationale, Eduscol) restent la référence.

## Licence

Code sous licence MIT (voir `LICENSE`).
