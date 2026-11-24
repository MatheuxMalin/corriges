"""Tests GIVEN / WHEN / THEN de verif.py.

Principe : chaque test recalcule la réponse PAR UNE AUTRE MÉTHODE que verif.py (opération inverse, valeur
remplacée, comptage sur 1 000 personnes…), puis la compare à ce que la vidéo affiche (`reponse`) ou calcule
(`valeur`, `etapes`). Si verif.py affichait un résultat faux, le test échouerait.

Lancer : python -m unittest -v
"""
import unittest
from fractions import Fraction as F

import sympy as sp

import verif

x = sp.symbols("x", real=True)
EXOS = {e["n"]: e for e in verif.tous()}


class MiseEnForme(unittest.TestCase):
    """Les fonctions d'affichage, testées sur des cas limites."""

    def test_nombre_exact(self):
        # GIVEN des fractions à écriture décimale finie, très longue, ou infinie
        # WHEN on les met en forme
        # THEN tous les chiffres sont gardés, la virgule est française, le moins est le vrai signe moins
        self.assertEqual(verif.nombre(F(1, 2048)), "0,00048828125")
        self.assertEqual(verif.nombre(F(-5)), "−5")
        self.assertEqual(verif.nombre(F(4, 7)), "4/7")
        self.assertEqual(verif.nombre(F(23, 2)), "11,5")

    def test_arrondi_ecole(self):
        # GIVEN des valeurs qui finissent par 5  WHEN on arrondit  THEN la moitié monte, comme en classe
        self.assertEqual(verif.arrondi(F(165, 10), 0), 17)
        self.assertEqual(verif.arrondi(F(1665, 100), 1), F(167, 10))
        self.assertEqual(verif.arrondi(F(-165, 10), 0), -17)

    def test_pourcentage_non_decimal(self):
        # GIVEN 1/6 (16,666… %)  WHEN on l'écrit sans préciser d'arrondi  THEN erreur ; avec arrondi  THEN « environ »
        with self.assertRaises(ValueError):
            verif.pct(F(1, 6))
        self.assertEqual(verif.pct(F(1, 6), decimales=1), "environ +16,7 %")

    def test_intervalles_et_droites(self):
        # GIVEN des ensembles sympy et des coefficients  WHEN on les écrit  THEN notation française
        self.assertEqual(verif.intervalle(sp.Interval.open(-1, 3)), "]−1 ; 3[")
        self.assertEqual(verif.intervalle(sp.Union(sp.Interval.Ropen(-2, -1), sp.Interval.Lopen(3, 4))),
                         "[−2 ; −1[ ∪ ]3 ; 4]")
        self.assertEqual(verif.droite(F(2, 3), -2), "y = (2/3)x − 2")
        self.assertEqual(verif.droite(1, 0), "y = x")


class Evolutions(unittest.TestCase):
    def test_01_valeur_finale(self):
        # GIVEN 80 € et +15 %  WHEN on ajoute 15 centièmes de 80  THEN 92 €, affiché « 92 € »
        self.assertEqual(F(80) + F(80) * 15 / 100, EXOS[1]["valeur"])
        self.assertEqual(EXOS[1]["reponse"], "92 €")

    def test_02_valeur_initiale(self):
        # GIVEN 48 € après −20 %  WHEN on rebaisse la réponse de 20 %  THEN on retrouve 48 €
        self.assertEqual(EXOS[2]["valeur"] * F(80, 100), 48)
        # et le piège 48 × 1,2, rebaissé de 20 %, ne redonne pas 48
        self.assertNotEqual(F(48) * F(12, 10) * F(80, 100), 48)
        self.assertEqual(EXOS[2]["reponse"], "60 €")

    def test_03_taux(self):
        # GIVEN 250 -> 300  WHEN on applique le taux affiché à 250  THEN 300
        self.assertEqual(250 * (1 + EXOS[3]["valeur"]), 300)
        self.assertEqual(EXOS[3]["reponse"], "+20 %")
        self.assertEqual(EXOS[3]["pieges"][0]["resultat"], "environ +16,7 %")

    def test_04_evolutions_successives(self):
        # GIVEN 100 €  WHEN +10 % puis −10 % (calcul en euros)  THEN 99 €, soit −1 %
        prix = F(100) * F(110, 100)
        prix = prix - prix / 10
        self.assertEqual(prix, 99)
        self.assertEqual((prix - 100) / 100, EXOS[4]["valeur"])
        self.assertEqual(EXOS[4]["reponse"], "−1 %")

    def test_05_taux_reciproque(self):
        # GIVEN 80 € (100 € baissé de 20 %)  WHEN on applique la hausse affichée  THEN retour à 100 €
        self.assertEqual(F(80) * (1 + EXOS[5]["valeur"]), 100)
        self.assertEqual(EXOS[5]["reponse"], "+25 %")


class Calcul(unittest.TestCase):
    def test_06_produit_nul(self):
        # GIVEN (2x − 6)(x + 5)  WHEN on remplace x par chaque solution affichée  THEN le produit vaut 0
        e = (2 * x - 6) * (x + 5)
        self.assertEqual([e.subs(x, v) for v in EXOS[6]["valeur"]], [0, 0])
        self.assertEqual(EXOS[6]["reponse"], "S = {−5 ; 3}")

    def test_07_signe_affine(self):
        # GIVEN −3x + 12  WHEN on évalue en 0, 4 et 10  THEN positif, nul, négatif, comme affiché
        e = -3 * x + 12
        self.assertTrue(e.subs(x, 0) > 0 and e.subs(x, 4) == 0 and e.subs(x, 10) < 0)
        self.assertEqual(EXOS[7]["valeur"], {"racine": 4, "signe avant": 1, "signe après": -1})
        self.assertEqual(EXOS[7]["reponse"], "positif pour x < 4, nul en 4, négatif pour x > 4")

    def test_08_signe_second_degre(self):
        # GIVEN (x − 1)(x + 2)  WHEN on évalue en −3, 0 et 2  THEN +, −, +, comme affiché
        e = (x - 1) * (x + 2)
        self.assertEqual([int(sp.sign(e.subs(x, v))) for v in (-3, 0, 2)], EXOS[8]["valeur"]["signes"])
        self.assertEqual(EXOS[8]["reponse"], "positif sur ]−∞ ; −2[ et sur ]1 ; +∞[, négatif sur ]−2 ; 1[")

    def test_09_developper(self):
        # GIVEN (2x − 3)²  WHEN on compare en trois valeurs de x à 4x² − 12x + 9  THEN égal ; et c'est l'affichage
        for v in (-2, 0, 5):
            self.assertEqual(((2 * x - 3) ** 2).subs(x, v), (4 * x**2 - 12 * x + 9).subs(x, v))
        self.assertEqual(EXOS[9]["reponse"], "4x² − 12x + 9")

    def test_10_factoriser(self):
        # GIVEN 4x² − 25  WHEN on développe (2x − 5)(2x + 5)  THEN on retrouve 4x² − 25 ; c'est l'affichage
        self.assertEqual(sp.expand((2 * x - 5) * (2 * x + 5)), 4 * x**2 - 25)
        self.assertEqual(EXOS[10]["reponse"], "(2x − 5)(2x + 5)")
        self.assertEqual(EXOS[10]["etapes"]["piège (2x − 5)² : terme en x"], -20)


class Fonctions(unittest.TestCase):
    def test_11_coefficient_directeur(self):
        # GIVEN A(1 ; 3), B(4 ; 9)  WHEN on avance de 3 avec la pente affichée depuis A  THEN on arrive en B
        self.assertEqual(3 + EXOS[11]["valeur"] * 3, 9)
        self.assertEqual(EXOS[11]["reponse"], "2")

    def test_12_equation_reduite(self):
        # GIVEN la droite affichée  WHEN x = 1  THEN y = 3 (A est sur la droite)
        v = EXOS[12]["valeur"]
        self.assertEqual(v["m"] * 1 + v["p"], 3)
        self.assertEqual(EXOS[12]["reponse"], "y = 2x + 1")

    def test_13_lecture(self):
        # GIVEN la droite affichée  WHEN x = 0 et x = 3  THEN −2 et 0 (les deux points lus sur le graphique)
        v = EXOS[13]["valeur"]
        self.assertEqual((v["m"] * 0 + v["p"], v["m"] * 3 + v["p"]), (-2, 0))
        self.assertEqual(EXOS[13]["reponse"], "y = (2/3)x − 2")

    def test_14_resolution_graphique(self):
        # GIVEN f(x) = x² − 2x − 2  WHEN on calcule f en chaque solution affichée  THEN 1
        f = x**2 - 2 * x - 2
        self.assertEqual([f.subs(x, v) for v in EXOS[14]["valeur"]], [1, 1])
        self.assertEqual(EXOS[14]["reponse"], "S = {−1 ; 3}")

    def test_15_inequation(self):
        # GIVEN f sur [−2 ; 4]  WHEN on teste un point dans S et aux bords  THEN f < 1 dedans, f ≥ 1 aux bornes
        f = x**2 - 2 * x - 2
        self.assertTrue(f.subs(x, 0) < 1 and f.subs(x, -1) == 1 and f.subs(x, 3) == 1)
        self.assertEqual(EXOS[15]["reponse"], "S = ]−1 ; 3[")
        # et le piège « au-dessus » commence en −2, car f(−2) = 6 > 1
        self.assertEqual(f.subs(x, -2), 6)
        self.assertEqual(EXOS[15]["pieges"][0]["resultat"], "[−2 ; −1[ ∪ ]3 ; 4]")


class Statistiques(unittest.TestCase):
    def test_16_moyenne(self):
        # GIVEN la série  WHEN on somme les écarts à la moyenne affichée  THEN 0
        self.assertEqual(sum(v - EXOS[16]["valeur"] for v in (12, 15, 9, 14, 10)), 0)
        self.assertEqual(EXOS[16]["reponse"], "12")

    def test_17_mediane(self):
        # GIVEN 6 valeurs  WHEN on compte les valeurs sous et sur la médiane affichée  THEN 3 et 3
        s, m = [3, 7, 8, 12, 15, 20], EXOS[17]["valeur"]
        self.assertEqual((sum(v < m for v in s), sum(v > m for v in s)), (3, 3))
        self.assertEqual(EXOS[17]["reponse"], "10")

    def test_18_ecart_interquartile(self):
        # GIVEN Q1 = 8 et Q3 = 15  WHEN on ajoute l'écart affiché à Q1  THEN Q3 ; et le piège vaut l'étendue 16
        self.assertEqual(8 + EXOS[18]["valeur"], 15)
        self.assertEqual(EXOS[18]["reponse"], "7")
        self.assertEqual(EXOS[18]["pieges"][0]["resultat"], "16")

    def test_19_secteur(self):
        # GIVEN un secteur de 72°  WHEN on multiplie la proportion affichée par 360  THEN 72
        self.assertEqual(EXOS[19]["valeur"] * 360, 72)
        self.assertEqual(EXOS[19]["reponse"], "0,2, soit 20 %")

    def test_20_moyenne_ponderee(self):
        # GIVEN notes et coefficients  WHEN on « déplie » les coefficients (8, 14, 14, 11, 11, 11)  THEN moyenne 11,5
        deplie = [8, 14, 14, 11, 11, 11]
        self.assertEqual(F(sum(deplie), len(deplie)), EXOS[20]["valeur"])
        self.assertEqual(EXOS[20]["reponse"], "11,5")


class Probabilites(unittest.TestCase):
    def test_21_22_23_arbre(self):
        # GIVEN 1 000 personnes : 300 dans A dont 150 dans B ; 700 hors de A dont 140 dans B
        # WHEN on compte  THEN P(A ∩ B) = 150/1000, P(B) = 290/1000, P_B(A) = 150/290
        self.assertEqual(EXOS[21]["valeur"], F(150, 1000))
        self.assertEqual(EXOS[22]["valeur"], F(150 + 140, 1000))
        self.assertEqual(EXOS[23]["valeur"], F(150, 290))
        self.assertEqual([EXOS[n]["reponse"] for n in (21, 22, 23)], ["0,15", "0,29", "15/29"])

    def test_24_25_tableau(self):
        # GIVEN la classe élève par élève (liste de 30 couples)  WHEN on compte  THEN les trois probabilités
        classe = [("F", "D")] * 12 + [("F", "E")] * 4 + [("G", "D")] * 9 + [("G", "E")] * 5
        fd = sum(e == ("F", "D") for e in classe)
        filles = sum(e[0] == "F" for e in classe)
        dp = sum(e[1] == "D" for e in classe)
        self.assertEqual(EXOS[24]["valeur"], F(fd, dp))
        self.assertEqual(EXOS[25]["valeur"], [F(fd, len(classe)), F(fd, filles), F(fd, dp)])
        self.assertEqual(EXOS[24]["reponse"], "4/7")
        self.assertEqual(EXOS[25]["reponse"], "P(F ∩ D) = 0,4 ; P_F(D) = 0,75 ; P_D(F) = 4/7")


class Ensemble(unittest.TestCase):
    def test_structure(self):
        # GIVEN la liste des exercices
        # WHEN on compte par bloc et on regarde pièges et étapes
        # THEN 25 exercices, 5 par bloc, chacun avec au moins un piège et une étape
        self.assertEqual(sorted(EXOS), list(range(1, 26)))
        blocs = [e["bloc"] for e in EXOS.values()]
        self.assertTrue(all(blocs.count(b) == 5 for b in set(blocs)))
        self.assertTrue(all(e["pieges"] and e["etapes"] for e in EXOS.values()))

    def test_aucun_tiret_comme_signe_moins(self):
        # GIVEN tout le texte affiché (réponses, pièges, étapes sérialisées)
        # WHEN on cherche un tiret « - » collé à un chiffre
        # THEN aucun : seul le vrai signe moins « − » est utilisé
        import re
        texte = str([verif.serialiser(e) for e in EXOS.values()])
        self.assertIsNone(re.search(r"(?<![\w])-\d", texte))


if __name__ == "__main__":
    unittest.main()
