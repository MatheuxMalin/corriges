"""Vérification des 25 exercices de la vidéo « Automatismes de Première ».

Exercices originaux, écrits pour la chaîne Matheux Malin, sur la liste des automatismes du programme de
spécialité mathématiques de Première (arrêté du 26-2-2026, BO n° 14 du 2 avril 2026). Aucun énoncé d'examen.

Pour chaque exercice, le programme calcule :
  - la réponse exacte (fractions ou sympy, jamais de nombre à virgule flottante) ;
  - chaque étape intermédiaire dite dans la voix off (rien n'est retapé à la main : les données de l'énoncé
    sont saisies une seule fois, puis tout en découle) ;
  - les erreurs fréquentes, avec le résultat faux qu'elles donnent (le « piège » expliqué dans la vidéo).

Usage : python verif.py  ->  preuves/exercices.json
"""
import json
import math
import os
import sys
from fractions import Fraction as F

import sympy as sp

# Variable réelle pour sympy : les élèves travaillent dans R, pas dans les complexes.
x = sp.symbols("x", real=True)

# Le vrai signe moins (U+2212), comme au tableau, et non le tiret « - » du clavier.
MOINS = "−"


# --------------------------------------------------------------------------------------------------------------
# Mise en forme à la française, exacte
# --------------------------------------------------------------------------------------------------------------

def decimal_fini(f):
    """Vrai si la fraction a une écriture décimale finie.

    Une fraction irréductible a une écriture décimale finie seulement si son dénominateur n'a que 2 et 5 comme
    facteurs premiers : 3/4 = 0,75, mais 4/7 = 0,571428… ne s'arrête jamais.
    """
    d = F(f).denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1


def nombre(f):
    """Fraction -> texte : écriture décimale exacte si elle existe (virgule française), sinon a/b.

    Calcul entièrement en entiers : on cherche k tel que f × 10^k soit entier, puis on place la virgule.
    Aucun passage par un flottant, donc aucun chiffre perdu.
    """
    f = F(f)
    signe = MOINS if f < 0 else ""
    f = abs(f)
    if not decimal_fini(f):
        return f"{signe}{f.numerator}/{f.denominator}"
    k = 0
    while (f * 10**k).denominator != 1:
        k += 1
    chiffres = str(int(f * 10**k)).rjust(k + 1, "0")
    if k == 0:
        return signe + chiffres
    return f"{signe}{chiffres[:-k]},{chiffres[-k:]}"


def arrondi(f, k):
    """Arrondi « comme à l'école » à k décimales : 16,65 -> 16,7 et 16,5 -> 17 (la moitié monte).

    round() de Python arrondit les moitiés au pair (16,5 -> 16) : ce n'est pas la règle enseignée.
    """
    f = F(f)
    signe = -1 if f < 0 else 1
    return signe * F(math.floor(abs(f) * 10**k + F(1, 2)), 10**k)


def pct(f, decimales=None, signe_plus=True):
    """Fraction (0,2 pour 20 %) -> texte en pourcentage : '+20 %', '−1 %', 'environ +16,7 %'.

    Si le pourcentage n'a pas d'écriture décimale finie, il faut dire à combien de décimales arrondir :
    le texte commence alors par « environ ».
    """
    v = F(f) * 100
    debut = ""
    if not decimal_fini(v):
        if decimales is None:
            raise ValueError(f"{v} % n'est pas décimal : préciser l'arrondi")
        v, debut = arrondi(v, decimales), "environ "
    plus = "+" if (signe_plus and v > 0) else ""
    return f"{debut}{plus}{nombre(v)} %"


def frac(r):
    """Nombre rationnel sympy (ou entier) -> Fraction, pour passer de sympy à l'arithmétique exacte."""
    r = sp.Rational(r)
    return F(int(r.p), int(r.q))


def ensemble(valeurs):
    """Liste de nombres -> 'S = {−5 ; 3}'."""
    return "S = {" + " ; ".join(nombre(frac(v)) for v in valeurs) + "}"


def borne(b):
    """Borne d'intervalle sympy -> texte (−∞, +∞ ou nombre)."""
    if b == -sp.oo:
        return f"{MOINS}∞"
    if b == sp.oo:
        return "+∞"
    return nombre(frac(b))


def intervalle(s):
    """Ensemble sympy (Interval ou réunion d'intervalles) -> notation française : ']−1 ; 3[', '[−2 ; −1[ ∪ ]3 ; 4]'.

    Crochet tourné vers l'extérieur = borne exclue (et toujours pour l'infini).
    """
    if isinstance(s, sp.Union):
        return " ∪ ".join(intervalle(i) for i in s.args)
    g = "]" if s.left_open else "["
    d = "[" if s.right_open else "]"
    return f"{g}{borne(s.start)} ; {borne(s.end)}{d}"


def droite(m, p):
    """Équation réduite y = mx + p -> texte : 'y = 2x + 1', 'y = (2/3)x − 2'."""
    m, p = F(m), F(p)
    if m == 1:
        terme = "x"
    elif m.denominator == 1:
        terme = f"{nombre(m)}x"
    else:
        terme = f"({nombre(m)})x"
    if p == 0:
        return f"y = {terme}"
    return f"y = {terme} {'+' if p > 0 else MOINS} {nombre(abs(p))}"


def polynome(expr):
    """Polynôme du second degré sympy -> texte : '4x² − 12x + 9' (termes nuls omis)."""
    a, b, c = (frac(v) for v in sp.Poly(sp.expand(expr), x).all_coeffs())
    texte = ""
    for coef, puissance in [(a, "x²"), (b, "x"), (c, "")]:
        if coef == 0:
            continue
        absolu = "" if (abs(coef) == 1 and puissance) else nombre(abs(coef))
        if not texte:
            texte = (MOINS if coef < 0 else "") + absolu + puissance
        else:
            texte += f" {'+' if coef > 0 else MOINS} {absolu}{puissance}"
    return texte


def ex(n, bloc, enonce, reponse, valeur, etapes, pieges):
    """Un exercice tel que la vidéo l'affiche et le dit.

    reponse : texte affiché à l'écran ; valeur : le résultat calculé (Fraction, liste, dict ou ensemble sympy) ;
    etapes : {étape dite dans la voix off : valeur exacte} ; pieges : [(erreur fréquente, résultat faux)].
    """
    return {"n": n, "bloc": bloc, "enonce": enonce, "reponse": reponse, "valeur": valeur, "etapes": etapes,
            "pieges": [{"erreur": e, "resultat": r} for e, r in pieges]}


# --------------------------------------------------------------------------------------------------------------
# Bloc 1 — Évolutions et variations
# Principe : une évolution de t % revient à multiplier par le coefficient multiplicateur (1 + t/100).
# --------------------------------------------------------------------------------------------------------------

def bloc_evolutions():
    """Exercices 1 à 5."""
    B = "Évolutions et variations"
    out = []

    # 1. Valeur finale : 80 × 1,15. À la main, on découpe 15 % = 10 % + 5 %.
    prix, t = F(80), F(15, 100)
    dix, cinq = prix / 10, prix / 20
    assert dix + cinq == prix * t
    fin = prix * (1 + t)
    out.append(ex(1, B, f"Un prix de {nombre(prix)} € augmente de {pct(t, signe_plus=False)}. Quel est le nouveau prix ?",
                  f"{nombre(fin)} €", fin,
                  {"10 % de 80": dix, "5 % de 80": cinq, "15 % de 80": dix + cinq, "coefficient": 1 + t,
                   "80 × 1,15": fin},
                  [("ajouter 15 € au lieu de 15 %", f"{nombre(prix + t * 100)} €")]))

    # 2. Valeur initiale : on DIVISE par le coefficient 0,8 (et on ne multiplie pas par 1,2).
    apres, t = F(48), F(20, 100)
    coef = 1 - t
    debut = apres / coef
    assert apres / 8 * 10 == debut  # diviser par 0,8 = diviser par 8 puis multiplier par 10
    out.append(ex(2, B, f"Après une baisse de {pct(t, signe_plus=False)}, un article coûte {nombre(apres)} €. "
                  "Quel était son prix avant la baisse ?", f"{nombre(debut)} €", debut,
                  {"coefficient": coef, "48 ÷ 8": apres / 8, "× 10": apres / 8 * 10,
                   "piège 48 × 1,2": apres * (1 + t), "20 % de 60": debut * t, "60 − 12": debut - debut * t},
                  [("remonter de 20 % : 48 × 1,2", f"{nombre(apres * (1 + t))} €")]))

    # 3. Taux d'évolution = (arrivée − départ) / départ.
    dep, arr = F(250), F(300)
    var = arr - dep
    taux = var / dep
    piege = var / arr
    out.append(ex(3, B, f"Une population passe de {nombre(dep)} à {nombre(arr)} habitants. "
                  "Quel est le taux d'évolution, en pourcentage ?", pct(taux), taux,
                  {"300 − 250": var, "50 ÷ 250": taux, "piège 50 ÷ 300": piege,
                   "piège en % arrondi au dixième": arrondi(piege * 100, 1), "250 × 1,2": dep * (1 + taux)},
                  [("diviser par la valeur d'arrivée : 50 ÷ 300", pct(piege, decimales=1))]))

    # 4. Évolutions successives : les coefficients se multiplient, les taux ne s'additionnent pas.
    t = F(10, 100)
    c = (1 + t) * (1 - t)
    out.append(ex(4, B, "Un prix augmente de 10 %, puis baisse de 10 %. Quelle est l'évolution globale ?",
                  pct(c - 1), c - 1,
                  {"1,1 × 0,9": c, "100 × 1,1": 100 * (1 + t), "10 % de 110": 100 * (1 + t) * t,
                   "110 − 11": 100 * (1 + t) * (1 - t)},
                  [("additionner les taux : +10 % − 10 %", pct(t - t))]))

    # 5. Taux réciproque : le coefficient qui compense 0,8 est 1/0,8 = 1,25.
    t = F(20, 100)
    reste = 100 * (1 - t)
    hausse = (100 - reste) / reste
    assert hausse == 1 / (1 - t) - 1
    out.append(ex(5, B, "Un prix baisse de 20 %. Quelle hausse faut-il appliquer pour revenir au prix de départ ?",
                  pct(hausse), hausse,
                  {"100 après −20 %": reste, "100 − 80": 100 - reste, "20 ÷ 80": hausse,
                   "piège 80 × 1,2": reste * (1 + t), "1 ÷ 0,8": 1 / (1 - t)},
                  [("prendre le même taux dans l'autre sens : +20 %", f"{nombre(reste * (1 + t))} € au lieu de 100 €")]))
    return out


# --------------------------------------------------------------------------------------------------------------
# Bloc 2 — Calcul numérique et algébrique (sympy pour résoudre, développer, factoriser)
# --------------------------------------------------------------------------------------------------------------

def signes_entre_racines(expr, racines):
    """Signe (+1 ou −1) de expr dans chaque intervalle délimité par les racines, de gauche à droite.

    On teste une valeur dans chaque intervalle : avant la première racine, entre deux racines, après la dernière.
    """
    r = sorted(racines)
    tests = [r[0] - 1] + [(a + b) / 2 for a, b in zip(r, r[1:])] + [r[-1] + 1]
    return [int(sp.sign(expr.subs(x, v))) for v in tests]


def mot_signe(s):
    """+1 -> 'positif', −1 -> 'négatif'."""
    return "positif" if s > 0 else "négatif"


def bloc_calcul():
    """Exercices 6 à 10."""
    B = "Calcul numérique et algébrique"
    out = []

    # 6. Équation produit nul : un produit est nul si et seulement si l'un de ses facteurs est nul.
    f1, f2 = 2 * x - 6, x + 5
    sols = sorted(sp.solve(f1, x) + sp.solve(f2, x))
    assert sols == sorted(sp.solve(f1 * f2, x))
    out.append(ex(6, B, "Résoudre (2x − 6)(x + 5) = 0.", ensemble(sols), [frac(s) for s in sols],
                  {"2x = 6 donne x": frac(sp.solve(f1, x)[0]), "x + 5 = 0 donne x": frac(sp.solve(f2, x)[0]),
                   "vérif 2 × 3 − 6": frac(f1.subs(x, 3))},
                  [("lire le 6 de la parenthèse au lieu de résoudre 2x = 6", ensemble([-5, 6]))]))

    # 7. Signe de a x + b : du signe de a à droite de la racine, du signe contraire à gauche.
    a, b = -3, 12
    e7 = a * x + b
    rac = frac(sp.solve(e7, x)[0])
    gauche, apres = signes_entre_racines(e7, [rac])
    r = nombre(rac)
    out.append(ex(7, B, "Donner le signe de −3x + 12 selon les valeurs de x.",
                  f"{mot_signe(gauche)} pour x < {r}, nul en {r}, {mot_signe(apres)} pour x > {r}",
                  {"racine": rac, "signe avant": gauche, "signe après": apres},
                  {"racine de −3x + 12": rac, "valeur en x = 0": frac(e7.subs(x, 0))},
                  [("oublier que le coefficient −3 est négatif",
                    f"{mot_signe(apres)} avant {r}, {mot_signe(gauche)} après")]))

    # 8. Signe d'une expression factorisée du second degré : tableau de signes.
    e8 = (x - 1) * (x + 2)
    r0, r1 = (frac(v) for v in sorted(sp.solve(e8, x)))
    signes = signes_entre_racines(e8, [r0, r1])
    assert signes == [1, -1, 1]  # la phrase ci-dessous suppose ce motif + − +
    out.append(ex(8, B, "Donner le signe de (x − 1)(x + 2) selon les valeurs de x.",
                  f"positif sur ]{MOINS}∞ ; {nombre(r0)}[ et sur ]{nombre(r1)} ; +∞[, "
                  f"négatif sur ]{nombre(r0)} ; {nombre(r1)}[",
                  {"racines": [r0, r1], "signes": signes},
                  {"racines": [r0, r1], "valeur en x = 0": frac(e8.subs(x, 0))},
                  [("se tromper de signe sur les racines", f"racines {nombre(-r1)} et {nombre(-r0)}")]))

    # 9. Identité remarquable (a − b)² = a² − 2ab + b², avec a = 2x et b = 3.
    e9 = (2 * x - 3) ** 2
    dev = sp.expand(e9)
    out.append(ex(9, B, "Développer et réduire (2x − 3)².", polynome(dev), polynome(dev),
                  {"(2x)² : coefficient": F(2**2), "double produit 2 × 2 × 3": F(2 * 2 * 3), "3²": F(3**2),
                   "vérif x = 1, (2 − 3)²": frac(e9.subs(x, 1)), "vérif x = 1, développé": frac(dev.subs(x, 1))},
                  [("oublier le double produit", polynome(4 * x**2 + 9)),
                   ("oublier d'élever le 2 au carré", polynome(2 * x**2 - 12 * x + 9))]))

    # 10. Différence de deux carrés : a² − b² = (a − b)(a + b), avec a = 2x et b = 5.
    ca, cb = 2, 5
    e10 = (ca * x) ** 2 - cb**2
    assert sp.expand((ca * x - cb) * (ca * x + cb)) == e10
    piege = sp.expand((ca * x - cb) ** 2)
    out.append(ex(10, B, "Factoriser 4x² − 25.", f"({ca}x {MOINS} {cb})({ca}x + {cb})", polynome(e10),
                  {"4x² = (2x)²": F(ca**2), "25 = 5²": F(cb**2),
                   "piège (2x − 5)² : terme en x": frac(piege.coeff(x, 1))},
                  [("écrire (2x − 5)²", f"{polynome(piege)} une fois développé")]))
    return out


# --------------------------------------------------------------------------------------------------------------
# Bloc 3 — Fonctions et représentations
# --------------------------------------------------------------------------------------------------------------

F_COURBE = x**2 - 2 * x - 2       # courbe tracée pour les exercices 14 et 15
DOMAINE = sp.Interval(-2, 4)      # elle est tracée sur [−2 ; 4]


def bloc_fonctions():
    """Exercices 11 à 15."""
    B = "Fonctions et représentations"
    out = []

    # 11. Coefficient directeur = variation des ordonnées / variation des abscisses.
    (xa, ya), (xb, yb) = (1, 3), (4, 9)
    dy, dx = F(yb - ya), F(xb - xa)
    m = dy / dx
    out.append(ex(11, B, f"Quel est le coefficient directeur de la droite passant par A({xa} ; {ya}) et B({xb} ; {yb}) ?",
                  nombre(m), m, {"9 − 3": dy, "4 − 1": dx, "6 ÷ 3": m, "piège 3 ÷ 6": dx / dy},
                  [("inverser le quotient : Δx ÷ Δy", nombre(dx / dy))]))

    # 12. Équation réduite par un point et le coefficient directeur : y = mx + p, puis p avec le point.
    m, (xa, ya) = F(2), (1, 3)
    p = ya - m * xa
    out.append(ex(12, B, f"Donner l'équation réduite de la droite de coefficient directeur {nombre(m)} "
                  f"passant par A({xa} ; {ya}).", droite(m, p), {"m": m, "p": p},
                  {"3 = 2 × 1 + p donne p": p, "vérif 2 × 1 + 1": m * xa + p},
                  [("prendre l'ordonnée de A comme ordonnée à l'origine", droite(m, ya))]))

    # 13. Lecture graphique : la droite passe par (0 ; −2) (sur l'axe des ordonnées) et par (3 ; 0).
    (x0, y0), (x1, y1) = (0, -2), (3, 0)
    assert x0 == 0  # le premier point est sur l'axe des ordonnées : son ordonnée est p
    m, p = F(y1 - y0, x1 - x0), F(y0)
    out.append(ex(13, B, "Lire l'équation réduite de la droite tracée (elle passe par (0 ; −2) et (3 ; 0)).",
                  droite(m, p), {"m": m, "p": p},
                  {"ordonnée à l'origine": p, "on avance de": F(x1 - x0), "on monte de": F(y1 - y0),
                   "coefficient directeur": m, "vérif (2/3) × 3 − 2": m * x1 + p},
                  [("prendre 3, lu sur l'axe des abscisses, comme ordonnée à l'origine", droite(m, x1))]))

    # 14. Résoudre graphiquement f(x) = 1 : abscisses des points de la courbe à la hauteur 1.
    k = 1
    s14 = sorted(sp.solve(sp.Eq(F_COURBE, k), x))
    zeros = sorted(sp.solve(F_COURBE, x))
    assert zeros == [1 - sp.sqrt(3), 1 + sp.sqrt(3)]
    approx = [arrondi(F(str(sp.N(z, 30))), 1) for z in zeros]  # 30 chiffres exacts, puis arrondi école
    out.append(ex(14, B, "Avec la courbe de f tracée, résoudre graphiquement f(x) = 1.", ensemble(s14),
                  [frac(s) for s in s14],
                  {f"f({nombre(frac(s))})": frac(F_COURBE.subs(x, s)) for s in s14},
                  [("lire où la courbe coupe l'axe des abscisses (c'est résoudre f(x) = 0)",
                    f"environ {nombre(approx[0])} et {nombre(approx[1])}")]))

    # 15. f(x) < 1 : la courbe strictement sous la droite y = 1 ; bornes exclues (inégalité stricte).
    s15 = sp.solve_univariate_inequality(F_COURBE < k, x, relational=False).intersect(DOMAINE)
    dessus = sp.solve_univariate_inequality(F_COURBE > k, x, relational=False).intersect(DOMAINE)
    out.append(ex(15, B, "Avec la même courbe, résoudre graphiquement f(x) < 1.", f"S = {intervalle(s15)}", s15,
                  {"f(1), le minimum": frac(F_COURBE.subs(x, 1)), "f(−2)": frac(F_COURBE.subs(x, -2)),
                   "f(4)": frac(F_COURBE.subs(x, 4))},
                  [("garder la partie de la courbe au-dessus de la droite", intervalle(dessus)),
                   ("fermer les crochets alors que l'inégalité est stricte", intervalle(s15.closure))]))
    return out


# --------------------------------------------------------------------------------------------------------------
# Bloc 4 — Statistiques
# --------------------------------------------------------------------------------------------------------------

def bloc_stats():
    """Exercices 16 à 20."""
    B = "Statistiques"
    out = []

    # 16. Moyenne = somme / nombre de valeurs ; vérification par les écarts, dont la somme est nulle.
    s = [12, 15, 9, 14, 10]
    moy = F(sum(s), len(s))
    out.append(ex(16, B, f"Calculer la moyenne de la série : {' ; '.join(map(str, s))}.", nombre(moy), moy,
                  {"somme": F(sum(s)), "nombre de valeurs": F(len(s)), "60 ÷ 5": moy,
                   "écarts à la moyenne": [v - moy for v in s], "piège 60 ÷ 4": F(sum(s), len(s) - 1),
                   "plus grande valeur": F(max(s))},
                  [("diviser par 4 au lieu de 5", nombre(F(sum(s), len(s) - 1)))]))

    # 17. Médiane d'une série de taille paire : moyenne des deux valeurs du milieu, série rangée.
    s = sorted([3, 7, 8, 12, 15, 20])
    i = len(s) // 2
    med = F(s[i - 1] + s[i], 2)
    out.append(ex(17, B, f"Donner la médiane de la série : {' ; '.join(map(str, s))}.", nombre(med), med,
                  {"valeurs du milieu": [F(s[i - 1]), F(s[i])], "8 + 12": F(s[i - 1] + s[i]), "20 ÷ 2": med},
                  [("prendre une seule valeur du milieu", f"{s[i - 1]} ou {s[i]}")]))

    # 18. Écart interquartile = Q3 − Q1 (largeur de la boîte) ; à ne pas confondre avec l'étendue.
    mini, q1, me, q3, maxi = 4, 8, 11, 15, 20
    eiq = F(q3 - q1)
    out.append(ex(18, B, f"Diagramme en boîte : min {mini} ; Q1 = {q1} ; médiane {me} ; Q3 = {q3} ; max {maxi}. "
                  "Donner l'écart interquartile.", nombre(eiq), eiq,
                  {"15 − 8": eiq, "médiane": F(me), "piège 20 − 4": F(maxi - mini)},
                  [("calculer l'étendue max − min", nombre(F(maxi - mini)))]))

    # 19. Diagramme circulaire : 360° représentent 100 %.
    angle = 72
    p = F(angle, 360)
    assert p.numerator == 1  # la proportion est « un cinquième » : la voix le dit ainsi
    out.append(ex(19, B, f"Dans un diagramme circulaire, un secteur mesure {angle}°. Quelle proportion représente-t-il ?",
                  f"{nombre(p)}, soit {pct(p, signe_plus=False)}", p,
                  {"5 × 72": F(p.denominator * angle), "72 ÷ 360": p, "dénominateur de la fraction": F(p.denominator)},
                  [("diviser par 100 au lieu de 360", f"{angle} %")]))

    # 20. Moyenne pondérée : somme des notes × coefficients, divisée par la somme des coefficients.
    notes, coefs = [8, 14, 11], [1, 2, 3]
    produits = [F(n * c) for n, c in zip(notes, coefs)]
    mp = sum(produits) / sum(coefs)
    out.append(ex(20, B, "Notes 8 (coefficient 1), 14 (coefficient 2) et 11 (coefficient 3). Moyenne ?",
                  nombre(mp), mp,
                  {"produits": produits, "somme des produits": sum(produits), "somme des coefficients": F(sum(coefs)),
                   "69 ÷ 6": mp, "piège 8 + 14 + 11": F(sum(notes)), "piège 33 ÷ 3": F(sum(notes), len(notes))},
                  [("faire la moyenne sans les coefficients", nombre(F(sum(notes), len(notes))))]))
    return out


# --------------------------------------------------------------------------------------------------------------
# Bloc 5 — Probabilités (arbre pondéré, puis tableau croisé d'effectifs)
# --------------------------------------------------------------------------------------------------------------

ARBRE = {"P(A)": F(3, 10), "P_A(B)": F(5, 10), "P_nonA(B)": F(2, 10)}
# Tableau croisé de la classe : filles demi-pensionnaires (FD), filles externes (FE), garçons (GD, GE)
TABLEAU = {"FD": 12, "FE": 4, "GD": 9, "GE": 5}


def bloc_probas():
    """Exercices 21 à 25."""
    B = "Probabilités"
    out = []
    pA, pB_A, pB_nA = ARBRE["P(A)"], ARBRE["P_A(B)"], ARBRE["P_nonA(B)"]

    # 21. Sur un chemin de l'arbre, on multiplie.
    pAB = pA * pB_A
    out.append(ex(21, B, f"Arbre : P(A) = {nombre(pA)} ; P_A(B) = {nombre(pB_A)} ; P_Ā(B) = {nombre(pB_nA)}. "
                  "Calculer P(A ∩ B).", nombre(pAB), pAB,
                  {"0,3 × 0,5": pAB, "piège 0,3 + 0,5": pA + pB_A},
                  [("additionner au lieu de multiplier le long du chemin", nombre(pA + pB_A))]))

    # 22. Probabilités totales : on additionne les chemins qui mènent à B.
    second = (1 - pA) * pB_nA
    pB = pAB + second
    out.append(ex(22, B, "Même arbre : calculer P(B).", nombre(pB), pB,
                  {"P(Ā)": 1 - pA, "0,7 × 0,2": second, "0,15 + 0,14": pB},
                  [("oublier le chemin qui passe par Ā", nombre(pAB))]))

    # 23. Probabilité « inversée » : P_B(A) = P(A ∩ B) / P(B).
    pA_B = pAB / pB
    out.append(ex(23, B, "Même arbre : calculer P_B(A).", nombre(pA_B), pA_B,
                  {"0,15 ÷ 0,29": pA_B},
                  [("confondre P_B(A) avec P_A(B), lu sur l'arbre", nombre(pB_A))]))

    # 24-25. Tableau croisé : « sachant » réduit la population, donc change le dénominateur.
    T = TABLEAU
    total, filles, dp = sum(T.values()), T["FD"] + T["FE"], T["FD"] + T["GD"]
    pF_et_D, pD_F, pF_D = F(T["FD"], total), F(T["FD"], filles), F(T["FD"], dp)
    out.append(ex(24, B, f"Tableau croisé ({total} élèves) : filles demi-pensionnaires {T['FD']}, filles externes "
                  f"{T['FE']}, garçons demi-pensionnaires {T['GD']}, garçons externes {T['GE']}. Probabilité d'être "
                  "une fille sachant qu'on est demi-pensionnaire ?", nombre(pF_D), pF_D,
                  {"total": F(total), "demi-pensionnaires 12 + 9": F(dp), "12 ÷ 21": pF_D, "piège 12 ÷ 30": pF_et_D},
                  [("diviser par l'effectif total", nombre(pF_et_D))]))
    out.append(ex(25, B, "Même tableau : donner P(F ∩ D), P_F(D) et P_D(F).",
                  f"P(F ∩ D) = {nombre(pF_et_D)} ; P_F(D) = {nombre(pD_F)} ; P_D(F) = {nombre(pF_D)}",
                  [pF_et_D, pD_F, pF_D],
                  {"filles 12 + 4": F(filles), "12 ÷ 30": pF_et_D, "12 ÷ 16": pD_F, "12 ÷ 21": pF_D},
                  [("utiliser le même dénominateur pour les trois", f"{T['FD']}/{total} partout")]))
    return out


def tous():
    """Les 25 exercices, dans l'ordre de la vidéo (5 par bloc du programme)."""
    return bloc_evolutions() + bloc_calcul() + bloc_fonctions() + bloc_stats() + bloc_probas()


# --------------------------------------------------------------------------------------------------------------
# Écriture des preuves
# --------------------------------------------------------------------------------------------------------------

def serialiser(v):
    """Valeur calculée -> forme lisible dans le JSON (et par les cartes) : nombres à la française, intervalles."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (F, int)):
        return nombre(v)
    if isinstance(v, (list, tuple)):
        return [serialiser(e) for e in v]
    if isinstance(v, dict):
        return {k: serialiser(e) for k, e in v.items()}
    if isinstance(v, (sp.Interval, sp.Union)):
        return intervalle(v)
    return v


def ecrire_preuves():
    """Écrit preuves/exercices.json et affiche les 25 réponses."""
    sys.stdout.reconfigure(encoding="utf-8")
    exos = tous()
    assert [e["n"] for e in exos] == list(range(1, 26))
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preuves")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "exercices.json"), "w", encoding="utf-8") as fh:
        json.dump([serialiser(e) for e in exos], fh, ensure_ascii=False, indent=2)
    for e in exos:
        print(f"{e['n']:>2}. {e['reponse']}")


if __name__ == "__main__":
    ecrire_preuves()
