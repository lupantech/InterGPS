#!/usr/bin/env python
# coding: utf-8

import os
import json
import re


##########################################
##### Simplify Question Text
##########################################

def simplify_text(text):
    """
    Remove nonsense words in text.
    E.g.
        text = "Find value of x."
        simplified_text = "Find x.
    """
    text = " " + text

    nonsense = ['GRIDIN', 'Suppose', 'below', 'exact', 'shown', 'composite', 'total', 'decimal', ' all ']
    nonsense += [' the ', ' this ', ' that ', ' its ', ' as (an |a |)', ' each ', ' then ', ' such ', 'given']
    nonsense += ['information', 'calculator', 'proportion']
    nonsense += ['exactly', 'respectively']
    nonsense += ['refer to', 'at right', ]
    nonsense += ['Express your answer in degrees.']
    nonsense += ['find in degrees.']
    nonsense += ['(square|) meters', '(square|) centimeters', '(square|) millimeters',
                 '(square|) inches', '(square|) feet', '(square|) units', '(square|) miles']
    nonsense += ['value of', 'variable of', 'variable']
    nonsense += ['solve problem', 'your answer']
    nonsense += ['in (diagram|figure)', 'use figure', 'use areas', 'use (an |a )']
    nonsense += ['area A of the shaded region is']
    nonsense += ['unless otherwise stated']
    nonsense += ['find indicated', 'find measure\.']
    nonsense += ['with side lengths indicated']

    for word in nonsense:
        pattern = re.compile(word, re.IGNORECASE)
        text = pattern.sub(" ", text)
        text = re.sub(r'[\s]+', r' ', text)

    # replace some phrased with standard text
    text = re.sub(r'area A of shaded region is', r'', text)
    text = re.sub(r'(cm|m|ft|in)\^2', r'', text)
    text = re.sub(r'what is|solve for|determine|solve|what it|how long is|Which polynomial best represents', r'Find',
                  text, flags=re.IGNORECASE)  # Note: flages=
    text = re.sub(r'to, find', r'to find', text)
    text = re.sub(r'Find \\angle', r'find m \\angle', text, flags=re.IGNORECASE)
    text = re.sub(r'measure of m', r'measure of', text, flags=re.IGNORECASE)
    text = re.sub(r'polygon figure', r'polygon', text)
    text = re.sub(r'express ', r'find ', text, flags=re.IGNORECASE)
    text = re.sub(r'figure (?=[A-Z]+)', r'', text)  # 428
    text = re.sub(r' an ', r' ', text)
    text = re.sub(r' of a ', r' of ', text)
    text = re.sub(r'is equal to', r'=', text)
    text = re.sub(r'(?<=\d) long(?![a-z])', r' ', text)
    text = re.sub(r'in terms of [a-z] and [a-z]', r' ', text)
    text = re.sub(r' is (?:an|a) (?=[a-z\d]{2})', r' is ', text)
    text = re.sub(r'triangle \\triangle', r'\\triangle', text, flags=re.IGNORECASE)
    text = re.sub(r'(m |)\\overrightarrow', r'', text)
    text = re.sub(r'(?<=[A-Z][A-Z]) \\cong (?=[A-Z][A-Z][\s\,\.\?])', r' = ', text)  # AB \cong EF -> AB = EF
    text = re.sub(r', and ', r' and ', text)
    text = re.sub(r'preimeter', r'perimeter', text)
    text = re.sub(r' (?=[\,\.\?])', r'', text)
    text = re.sub(r' side length ', r' side ', text)
    text = re.sub(r'triangle \\triangle', r'triangle', text)
    text = re.sub(r'(?<=\\angle [A-Z]{3}) \\cong (?=\\angle [A-Z]{3})', r' = ', text)
    text = re.sub(r'(?<=\\angle [A-Z\d]) \\cong (?=\\angle [A-Z\d])', r' = ', text)
    text = re.sub(r'BY = CZ = AX = 2.5 diameter of \\odot G = 5', r'BY = CZ = AX = 2.5, diameter of \\odot G = 5',
                  text)  # error, 977
    text = re.sub(r'=', r' = ', text)

    text = re.sub(r'[\s]+', r' ', text)
    text = text.strip()

    return text


##########################################
##### Match Specific Facts
##########################################

def Match_Facts(text):
    # Assume any segment appears to be tangent is tangent
    fact = r"(Assume |)(any |)segment(s|) (appears |appear |)(to be |)(tangent |)(are|is) tangent"
    target = r'[Tangent(Line($),Circle($))]'
    text = re.sub(fact, target, text, re.IGNORECASE)

    # Assume polygons appear to be regular are regular.
    fact = r"(Assume |)(any |)polygon(s|) (appears |appear |)(to be |)(regular |)(are|is) regular"
    target = r'[Regular(Polygon($))]'
    text = re.sub(fact, target, text, re.IGNORECASE)

    # pair of polygons is similar --> Similar(Polygon($),Polygon($))
    fact = r"(pair of |)polygons (is|are) similar"
    target = r'[Similar(Polygon($1),Polygon($2))]'
    text = re.sub(fact, target, text, flags=re.IGNORECASE)

    # Two triangles are similar -> Similar(Triangle($),Triangle($))
    fact2 = r"two triangles are similar"
    target2 = r'[Similar(Triangle($1),Triangle($2))]'
    text = re.sub(fact2, target2, text, flags=re.IGNORECASE)

    # For similar figures -> Simialr(Shape($),Shape($)
    pattern3 = r'for (pair of |)similar figures'
    target3 = r'[Similar(Shape($1),Shape($2))]'
    text = re.sub(pattern3, target3, text, flags=re.IGNORECASE)

    # Assume all polygons appear to be regular are regular. -> IsRegular(Polygon($))
    fact = r"Assume all polygons appear to be regular are regular."
    target = r'[IsRegular(Polygon($))]'
    text = re.sub(fact, target, text, re.IGNORECASE)

    # altitude drawn to hypotenuse.
    pattern = re.compile(r'altitude drawn to hypotenuse')
    target = r'altitude of [Triangle($1,$2,$3)], [Line($1,$3)] is hypotenuse of [Triangle($1,$2,$3)]'
    text = re.sub(pattern, target, text)

    return text


##########################################
##### Split and Reorganize Sentences
##########################################

# [S1]
def Split_Shapes(text):
    # Points S, T, and U are midpoints of DE, EF, and DF
    pattern = re.compile(r'([a-zA-Z]{4,})s ([A-Z]+), ([A-Z]+)(?: and|,) ([A-Z]+)(?=[\s\,\.\?])')
    target = r'\1 \2, \1 \3 and \1 \4'
    text = re.sub(pattern, target, text)

    # Polygons FGHJK and VWXUZ
    pattern = re.compile(r'([a-zA-Z]{4,})s ([A-Z]+) and ([A-Z]+)(?=[\s\,\.\?])')
    target = r'\1 \2 and \1 \3'
    text = re.sub(pattern, target, text)

    # Two triangles are similar.
    pattern = re.compile(r'(?:[T|t]wo) ([a-z]{3,})s are ([a-z]{3,})(?=[\s\,\.\?])')
    target = r'\1 is \2 \1'
    text = re.sub(pattern, target, text)

    # For what x is ABCD a parallelogram.
    pattern = re.compile(r'(?:[F|f]or what) ([a-z]) is (\w+) (?:a |)([a-z]+)(?=[\s\,\.\?])')
    target = r'\2 is \3, find \1'
    text = re.sub(pattern, target, text)

    # \angle 1A2B3C is intersected by parallel lines 4l and 5m
    pattern = re.compile(r'\\angle (A)(B)(C) is intersected by parallel lines ([a-z]) and ([a-z])(?=[\s\,\.\?])')
    target = r'\\angle \1\2\3. line \4 is parallel to line \5. line \4 and line \5 intersect at point \2'
    text = re.sub(pattern, target, text)

    # 1Radius 2OB 3is perpendicular to 4chord 5CD which is 6|2.
    pattern = re.compile(r'(\w+) ([A-Z]{2}) ([\w\s]+) (\w+) ([A-Z]{2}) which is (\S+)(?=[\s\,\.\?])')
    target = r'\2 is \1. \5 is \4. \2 \3 \5. \5 is \6'
    text = re.sub(pattern, target, text)

    return text


# [S2.1]
def Split_Shape_Has_Of(text):
    # [Circle(A)] has diameter [Line(A,C)] and diameter [Line(A,C)].
    pattern = re.compile(r'(\[\S+\]) has ([a-z]{3,}) (\[\S+\]) and ([a-z]{3,}) (\[\S+\])(?=[\s\,\.\?])')
    target = r'\3 is \2 of \1, \5 is \4 of \1'
    text = re.sub(pattern, target, text)

    # [Circle(O)] has a radius of 10
    pattern = re.compile(r'\[(\S+)\] has (?:a |an |)([a-z]{3,}) of (\d+)(?=[\s\,\.\?])')
    target = r'\2 of [\1] = \3'
    text = re.sub(pattern, target, text)

    # [Circle(A)] has diameter of [Line(D,F)]
    pattern = re.compile(r'\[(\S+)\] has (?:a |an |)([a-z]{3,}) of \[(\S+)\](?=[\s\,\.\?])')
    target = r'[\3] is \2 of [\1]'
    text = re.sub(pattern, target, text)

    # [Circle($)] having/with a diameter of 14
    pattern = re.compile(r'\[(\S+)\] (?:having |with |of |)(?:a |an |)([a-z]{3,}) (?:of|with) (\d+)(?=[\s\,\.\?])')
    target = r'[\1], \2 of [\1] = \3'
    text = re.sub(pattern, target, text)

    # 1[Trapezoid(R,S,T,V)] with 2base 3[Line(R,V)] and 4base 5[Line(S,T)] and 6median 7[Line(M,N)]
    pattern = re.compile(
        r'(\[\S+\]) with ([a-z]{3,}) (\[\S+\]) and ([a-z]{3,}) (\[\S+\]) and ([a-z]{3,}) (\[\S+\])(?=[\s\,\.\?])')
    target = r'\3 is \2 of \1, \5 is \4 of \1, \7 is \6 of \1'
    text = re.sub(pattern, target, text)

    # 1[Trapezoid(R,S,T,V)] with 2base 3[Line(R,V)] and 4base 5[Line(S,T)]
    pattern = re.compile(r'(\[\S+\]) with ([a-z]{3,}) (\[\S+\]) and ([a-z]{3,}) (\[\S+\])(?=[\s\,\.\?])')
    target = r'\3 is \2 of \1, \5 is \4 of \1'
    text = re.sub(pattern, target, text)

    # [Circle(F)] with diameter [Line(A,C)]
    pattern = re.compile(
        r'\[(\S+)\] (?:with|having) (?:a |an |)([a-z]{3,})(?<!s) (?:of |with |)\[(\S+)\](?=[\s\,\.\?])')
    target = r'[\1], [\3] is \2 of [\1]'
    text = re.sub(pattern, target, text)

    # 1[Square($)] with 25-centimeter 3sides 4is inscribed in 5[Circle($)].
    pattern = re.compile(r'(\[\S+\]) with (\d+)(?:-[a-z]{3,}) ([a-z]{3,})s ([a-z\s]+) (\[\S+\])(?=[\s\,\.\?])')
    target = r'\3 of \1 is \2, \1 \4 \5'
    text = re.sub(pattern, target, text)

    return text


# [S2.2]
def Split_In_A_B_Is_C(text):
    # In 1regular 2[hexagon()], 3side is 412
    pattern = re.compile(r'(?:In | in |For | for |)([a-z]+ |)\[(\S+)\], ([a-z]+) is (\d+)(?=[\,\.]| and)')
    target = r'\1 [\2], \3 of [\2] is \4'
    text = re.sub(pattern, target, text)

    # In 1regular 2[Triangle(A,C,E)], 3P is 4centroid.
    pattern = re.compile(r'(?:In | in |For | for |)([a-z]+ |)\[(\S+)\], ([A-Z]+) is ([a-z]{3,})(?=[\,\.]| and)')
    target = r'\1 [\2], \3 is \4 of [\2]'
    text = re.sub(pattern, target, text)

    # In [Triangle(A,B,C)], [Line(B,D)] is median.
    pattern = re.compile(r'(?:In | in |For | for |)\[(\S+)\], \[(\S+)\] is ([a-z]{3,})(?=[\,\.]| and)')
    target = r'[\1], [\2] is \3 of [\1]'
    text = re.sub(pattern, target, text)

    # In [Triangle(A,B,C)], [Line(A,D)] and [Line(D,C)] are angle bisectors
    pattern = re.compile(
        r'(?:In | in |For | for |)\[(\S+)\], \[(\S+)\] and \[(\S+)\] are ([a-z]{3,}) ([a-z]{3,})s(?=[\,\.]| and)')
    target = r'[\1], [\2] is \4 \5 of [\1], [\3] is \4 \5 of [\1]'
    text = re.sub(pattern, target, text)

    # In [Circle(O)], [Line(E,C)] and [Line(A,B)] are diameters
    pattern = re.compile(
        r'(?:In | in |For | for |circles)\[(\S+)\], \[(\S+)\] and \[(\S+)\] are ([a-z]{3,})s(?=[\,\.]| and)')
    target = r'[\1], [\2] is \4 of [\1], [\3] is \4 of [\1]'
    text = re.sub(pattern, target, text)

    # For [Trapezoid(Q,R,T,U)], V and S are midpoints of legs.
    pattern = re.compile(
        r'(?:In | in |For | for |)\[(\S+)\], ([A-Z]+) and ([A-Z]+) are ([a-z]{3,})s of ([a-z]{3,})s(?=[\,\.]| and)')
    target = r'[\1], \2 is \4 of \5 of [\1], \3 is \4 of \5 of [\1],'
    text = re.sub(pattern, target, text)

    # For [Isosceles(Trapezoid(X,Y,Z,W))], find length of median.
    pattern = re.compile(r'(?:In | in |For | for |)(\[\S+\]), find (?:length of |)([a-z]{3,})(?=[\,\.]| and)')
    target = r'\1, find \2 of \1'
    text = re.sub(pattern, target, text)

    return text


# [S2.3]
def Split_Eqs_ABC(text):
    # [(Angle(A)] \cong [(Angle(B)] \cong [(Angle(C)] \cong [(Angle(D)].
    pattern = re.compile(r'(\[\S+\]) (\\cong|=) (\[\S+\]) (\\cong|=) (\[\S+\]) (\\cong|=) (\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 \2 \3, \3 \4 \5, \5 \6 \7'
    text = re.sub(pattern, target, text)

    # [XX] = [YY] = [ZZ] = 12.5,
    pattern = re.compile(r'(\[\S+\]) = (\[\S+\]) = (\[\S+\]) = (\S+)(?=[\s\,\.\?])')
    target = r'\1 = \4, \2 = \4, \3 = \4'
    text = re.sub(pattern, target, text)

    # [(Angle(A)] \cong [(Angle(B)] \cong [(Angle(C)]
    pattern = re.compile(r'(\[\S+\]) (\\cong|=) (\[\S+\]) (\\cong|=) (\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 \2 \3, \3 \4 \5'
    text = re.sub(pattern, target, text)

    # [YY] = [ZZ] = 12.5,
    pattern = re.compile(r'(\[\S+\]) = (\[\S+\]) = (\S+)(?=[\s\,\.\?])')
    target = r'\1 = \3, \2 = \3'
    text = re.sub(pattern, target, text)

    return text


# [S2.4]
def Split_Shapes_ABC(text):
    # [Line(A,B)], [Line(B,C)], [Line(C,D)] and [Line(A,D)] are tangent to [Circle($)].
    pattern = re.compile(
        r'(\[\S+\]), (\[\S+\]), (\[\S+\]) and (\[\S+\]) are ([a-z]{3,}) ([a-z]{2,}) (\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 is \5 \6 \7, \2 is \5 \6 \7, \3 is \5 \6 \7, \4 is \5 \6 \7'
    text = re.sub(pattern, target, text)

    # [Point(S)], [Point(T)] and [Point(U)] are midpoints of [Line(D,E)], [Line(E,F)] and [Line(D,F)]
    pattern = re.compile(
        r'(\[\S+\]), (\[\S+\]) and (\[\S+\]) are ([a-z]{3,})s of (\[\S+\]), (\[\S+\]) and (\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 is \4 of \5, \2 is \4 of \6, \3 is \4 of \7,'
    text = re.sub(pattern, target, text)

    # [Line(J,H)], [Line(J,P)] and [Line(P,H)] are midsegments of [Triangle(K,L,M)].
    pattern = re.compile(r'(\[\S+\]), (\[\S+\]) and (\[\S+\]) are ([a-z]{3,})s of (\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 is \4 of \5, \2 is \4 of \5, \3 is \4 of \5,'
    text = re.sub(pattern, target, text)

    # diameters of [Circle(A)], [Circle(B)] and [Circle(C)] are 8, 18 and 11,
    pattern = re.compile(r'([a-z]+)s of \[(\S+)\], \[(\S+)\] and \[(\S+)\] are (\d+), (\d+) and (\d+)(?=[\s\,\.\?])')
    target = r'\1 of [\2] is \5, \1 of [\3] is \6, \1 of [\4] is \7,'
    text = re.sub(pattern, target, text)

    # J, P and L are midpoints of [Line(K,H)], [Line(H,M)] and [Line(M,K)]
    pattern = re.compile(
        r'([A-Z]), ([A-Z]) and ([A-Z]) are ([a-z]{3,})s of (\[\S+\]), (\[\S+\]) and (\[\S+\])(?=[\s\,\.\?])')
    target = r'[Point(\1)] is \4 of \5, [Point(\2)] is \4 of \6, [Point(\3)] is \4 of \7,'
    text = re.sub(pattern, target, text)

    # Lines 1l, 2m and 3n are 4perpendicular bisectors of 5[Triangle(K,L,M)] and 6meet at T.']
    pattern = re.compile(
        r'(?:[A-Za-z][a-z]{3,}s) ([a-z]), ([a-z]) and ([a-z]) are ([a-z]{3,} [a-z]{3,})s of (\[\S+\]) and ([\w\s]+)(?=[\s\,\.\?])')
    target = r'\1 is \4 of \5, \2 is \4 of \5, \3 is \4 of \5. \1, \2 and \3 \6'
    text = re.sub(pattern, target, text)

    # Lines 1l, 2m and 3n are 4perpendicular bisectors of 5[Triangle(K,L,M)]']
    pattern = re.compile(
        r'(?:[A-Za-z][a-z]{3,}s) ([a-z]), ([a-z]) and ([a-z]) are ([a-z]{3,} [a-z]{3,})s of (\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 is \4 of \5, \2 is \4 of \5, \3 is \4 of \5'
    text = re.sub(pattern, target, text)

    return text


# [S2.5]
def Split_Shapes_AB(text):
    # [Line(E,C)] and [Line(A,B)] are diameters of [Circle(O)],
    pattern = re.compile(r'(\[\S+\]) and (\[\S+\]) are ([a-z]+)s (?:of |)(\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 is \3 of \4, \2 is \3 of \4'
    text = re.sub(pattern, target, text)

    # [Triangle(F,G,H)] and [Triangle(F,H,J)] are inscribed in [Circle(K)]
    pattern = re.compile(r'(\[\S+\]) and (\[\S+\]) are ([a-z]{5,}) ([a-z]{2}) (\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 is \3 \4 \5, \2 is \3 \4 \5'
    text = re.sub(pattern, target, text)

    # [Circle(A)] has diameters [Line(D,F)] and [Line(P,G)].
    pattern = re.compile(r'(\[\S+\]) has ([a-z]+)s (?:of |)(\[\S+\]) and (\[\S+\])(?=[\s\,\.\?])')
    target = r'\1 has \2 of \3, \1 has \2 of \4'
    text = re.sub(pattern, target, text)

    # [Line(E,C)] and [Line(A,B)] are diameters,
    pattern = re.compile(r'(\[\S+\]) and (\[\S+\]) are ([a-z]+)s(?=[\s\,\.\?])')
    target = r'\1 is \3, \2 is \3'
    text = re.sub(pattern, target, text)

    # 1Chord 2[Line(J,F)] and 3Chord 4[Line(B,C)] 5intersect at K.
    pattern = re.compile(r'([\w]+) (\[\S+\]) and ([\w]+) (\[\S+\]) ([\w\s]+)(?=[\,\.\?])')
    target = r'\1 \2, \3 \4. \2 and \4 \5'
    text = re.sub(pattern, target, text)

    return text


# [S2.6]
def Split_Specials(text):
    # [Line(W,P)] is median and angle bisector
    pattern = re.compile(r'(\[\S+\]) is ([a-z]{3,}) and ([a-z]{3,}) ([a-z]{3,})(?=[\s\,\.\?])')
    target = r'\1 is \2, \1 is \3 \4'
    text = re.sub(pattern, target, text)

    # [Angle(3)] at vertex C
    pattern = re.compile(r'(\[\S+\]) at vertex (?:\[Point\(|)([A-Z])(?:\)\]|)(?=[\s\,\.\?])')
    target = r'\1, \1 = [Angle(\2)]'
    text = re.sub(pattern, target, text)

    # A [Square($)] is inscribed in [Circle($)] of area 18\pi.
    pattern = re.compile(r'(\[\S+\]) is ([a-z]{5,} [a-z]{1,5}) (\[\S+\]) of ([a-z]{3,}) (\S+)(?=[\s\,\.\?])')
    target = r'\1 is \2 \3, \4 of \1 is \5'
    text = re.sub(pattern, target, text)

    # [Rhombus(ABCD)] is circumscribed about [Circle(P)] and has perimeter of 32.
    pattern = re.compile(
        r'(\[\S+\]) is ([a-z]{5,} [a-z]{1,5}) (\[\S+\]) and has (?:a |)([a-z]{3,}) of (\S+)(?=[\s\,\.\?])')
    target = r'\1 is \2 \3, \4 of \1 is \5'
    text = re.sub(pattern, target, text)

    # diagonals of [Rectangle(ABCD)] have a length of 56.
    pattern = re.compile(
        r'diagonals of \[([\w]+)\(([A-Z])\,([A-Z])\,([A-Z])\,([A-Z])\)\] have (?:a |)length of (\d+)(?=[\.\,\?\s])')
    target = r'[\1(\2,\3,\4,\5)], [Line(\2,\4)] is diagonal of [\1(\2,\3,\4,\5)], [Line(\3,\5)] is diagonal of [\1(\2,\3,\4,\5)], length of [Line(\2,\4)] is \6, length of [Line(\3,\5)] is \6'
    text = re.sub(pattern, target, text)

    # diagonals of [Rhombus(F,G,H,J)] intersect at K
    pattern = re.compile(r'diagonals of \[([\w]+)\(([A-Z])\,([A-Z])\,([A-Z])\,([A-Z])\)\](?=[\.\,\?\s])')
    target = r'[\1(\2,\3,\4,\5)]. [Line(\2,\4)] is diagonal of [\1(\2,\3,\4,\5)], [Line(\3,\5)] is diagonal of [\1(\2,\3,\4,\5)]. [Line(\2,\4)] and [Line(\3,\5)]'
    text = re.sub(pattern, target, text)

    # A [Square($)] with side of 9 is inscribed in [Circle(J)].
    pattern = re.compile(r'(\[\S+\]) with ([a-z]{3,}) (?:of |)(\d+) is ([a-z]{5,} [a-z]{2,}) (\[\S+\])(?=[\.\,\?\s])')
    target = r'\2 of \1 is \3, \1 is \4 \5'
    text = re.sub(pattern, target, text)

    return text


##########################################
##### Geometric Shapes (Level-1)
##########################################

# [1.1]
def Match_Point(text):
    # Point A -> Point(A)
    pattern = re.compile(r'(?<![\S])([P|p]oint) ([A-Z\d])(?=[\.\,\?\s])')
    target = r'[Point(\2)]'
    text = re.sub(pattern, target, text)

    return text


# [1.2]
def Match_Line(text):
    # BC. -> Line(B,C)
    pattern = re.compile(r'(?<!\\widehat )(?<![A-Z])([S|s]egment |[S|s]ide )?([A-Z])([A-Z])(?![A-Z])')
    target = r'[Line(\2,\3)]'
    text = re.sub(pattern, target, text)

    # line l -> Line(l)
    pattern = re.compile(r'(?<!\w)[L|l]ine ([a-z])(?=[\.\,\?\s])')
    target = r'[Line(\1)]'
    text = re.sub(pattern, target, text)

    # m \parallel n. -> Line(m), Line(n)
    pattern = re.compile(r'(?<!\w)([a-z]) (\\[a-z]+) ([a-z])(?=[\.\,\?\s])')
    target = r'[Line(\1)] \2 [Line(\3)]'
    text = re.sub(pattern, target, text)

    # segment -> Line($)
    pattern = re.compile(r'(?<!\w)[S|s]egment(?=[\.\,\?\s])')
    target = r'[Line($)]'
    text = re.sub(pattern, target, text)

    return text


# [1.3]
def Match_Angle(text):
    # \angle ABC -> Angle(A,B,C)
    pattern = re.compile(r'\\angle ([A-Z])([A-Z])([A-Z])')
    target = r'[Angle(\1,\2,\3)]'
    text = re.sub(pattern, target, text)

    # \angle A -> Angle(A)
    pattern = re.compile(r'\\angle ([A-Z]|[\d]{1,2})(?=[\.\,\?\s])')
    target = r'[Angle(\1)]'
    text = re.sub(pattern, target, text)

    # find Z.
    pattern = re.compile(r'(?<=[F|f]ind )([A-Z])(?=[\.\,\?\s])')
    target = r'[Angle(\1)]'
    text = re.sub(pattern, target, text)

    # angle -> Angle($)
    pattern = re.compile(
        r'(?<![T|t]ri)(?<!rect)(central angle|interior angle|angle)(?! measure)(?! bisector)(?=[\.\,\?\s])')
    target = r'[Angle($)]'
    text = re.sub(pattern, target, text, re.IGNORECASE)

    return text


# [1.4]
def Match_Triangle(text):
    # \triangle ABC -> Triangle(A,B,C)
    pattern = re.compile(r'(\\|)([T|t]riangle) ([A-Z])([A-Z])([A-Z])(?=[\.\,\?\s])')
    target = r'[Triangle(\3,\4,\5)]'
    text = re.sub(pattern, target, text)

    # ABC -> Triangle(A,B,C)
    pattern = re.compile(r'(?<!\\widehat )(?<!\\wite )(?<![A-Z])([A-Z])([A-Z])([A-Z])(?=[\s\,\.\?])')
    target = r'[Triangle(\1,\2,\3)]'
    text = re.sub(pattern, target, text)

    # 45-45-90 triangle, 30-60-90 triangle
    pattern = re.compile(r"(\d+)\-(\d+)\-(\d+) triangle")
    target = r"[Triangle($1,$2,$3)], [Equals(MeasureOf(Angle($1)),\1)], [Equals(MeasureOf(Angle($2)),\2)], [Equals(MeasureOf(Angle($3)),\3)]"
    text = re.sub(pattern, target, text)

    # Triangles FGH and FHJ
    pattern = re.compile(r'([T|t]riangles) ([A-Z])([A-Z])([A-Z]) and ([A-Z])([A-Z])([A-Z])')
    target = r'[Triangle(\2,\3,\4)] and [Triangle(\5,\6,\7)]'
    text = re.sub(pattern, target, text)

    # in triangle. -> Triangle($), triangle is -> Triangle($)
    pattern = re.compile(r'[T|t]riangle(?=[\s\,\.\?])')
    target = r'[Triangle($)]'
    text = re.sub(pattern, target, text)

    return text


## [1.5-1.11]
def Match_Quadrilateral(text):
    # Case0: quadrilateral is parallelogram.
    fact = r"quadrilateral is parallelogram."
    target = r'[Parallelogram($)]'
    text = re.sub(fact, target, text, re.IGNORECASE)

    # Case1: ABCD is quadrilateral
    """
    ABCD is quadrilateral -> Quadrilateral(A,B,C,D)
    ABCD is parallelogram -> Parallelogram(A,B,C,D)
    ABCD is rhombus -> Rhombus(A,B,C,D)
    ABCD is trapezoid -> Trapezoid(A,B,C,D)
    ABCD is square -> Square(A,B,C,D)
    (Quadrilateral) ABCD is rectangle -> Rectangle(A,B,C,D)
    ABCD is kite -> Kite(A,B,C,D)
    """

    def repl_method(match):
        quad = match.group(5)  # 'rhombus'
        A = match.group(1)  # 'A'
        B = match.group(2)  # 'B'
        C = match.group(3)  # 'C'
        D = match.group(4)  # 'D'
        text = " [{}({},{},{},{})]".format(quad.capitalize(), A, B, C, D)
        return text

    pattern = re.compile(
        r'(?:[q|Q]uadrilateral\s|\s|)([A-Z])([A-Z])([A-Z])([A-Z]) is (quadrilateral|parallelogram|rhombus|trapezoid|square|rectangle|kite)')
    text = re.sub(pattern, repl_method, text)

    # Case2: quadrilateral ABCD
    """
    quadrilateral ABCD -> Quadrilateral(A,B,C,D)
    parallelogram ABCD -> Parallelogram(A,B,C,D)
    rhombus ABCD -> Rhombus(A,B,C,D)
    trapezoid ABCD -> Trapezoid(A,B,C,D)
    square ABCD -> Square(A,B,C,D)
    rectangle ABCD -> Rectangle(A,B,C,D)
    kite ABCD -> Kite(A,B,C,D)
    """

    def repl_method(match):
        quad = match.group(1)  # 'rhombus'
        A = match.group(2)  # 'A'
        B = match.group(3)  # 'B'
        C = match.group(4)  # 'C'
        D = match.group(5)  # 'D'
        text = "[{}({},{},{},{})]".format(quad.capitalize(), A, B, C, D)
        return text

    pattern = re.compile(
        r'(?:\\|)([q|Q]uadrilateral|[p|P]arallelogram|[r|R]hombus|[t|T]rapezoid|[s|S]quare|[r|R]ectangle|[k|K]ite) ([A-Z])([A-Z])([A-Z])([A-Z])(?=[\.\,\?\s])')
    text = re.sub(pattern, repl_method, text)

    # Case2': quadrilateral A
    def repl_method(match):
        quad = match.group(1)  # 'rhombus'
        A = match.group(2)  # 'A'
        text = "[{}({})]".format(quad.capitalize(), A)
        return text

    pattern = re.compile(
        r'(?:\\|)([q|Q]uadrilateral|[p|P]arallelogram|[r|R]hombus|[t|T]rapezoid|[s|S]quare|[r|R]ectangle|[k|K]ite) ([A-Z])(?=[\.\,\?\s])')
    text = re.sub(pattern, repl_method, text)

    # Case3: quadrilateral ABCD
    """
    ABCD -> Quadrilateral(A,B,C,D)
    polygon ABCD -> Quadrilateral(A,B,C,D)
    """
    pattern = re.compile(r'(?:[P|p]olygon |)(?<![A-Z])([A-Z])([A-Z])([A-Z])([A-Z])(?![A-Z])(?=[\.\,\?\s])')
    target = r'[Quadrilateral(\1,\2,\3,\4)]'
    text = re.sub(pattern, target, text)

    # Case4: the quadrilateral is parallelogram
    def repl_method(match):
        shape = match.group(1)  # 'rhombus'
        text = "[{}($)]".format(shape.capitalize(), shape)
        return text

    pattern = re.compile(r'quadrilateral is (parallelogram|rhombus|trapezoid|square|rectangle|kite)')
    text = re.sub(pattern, repl_method, text)

    # Case5: quadrilateral (1)
    """
    quadrilateral -> Quadrilateral($)
    parallelogram -> Parallelogram($)
    rhombus -> Rhombus($)
    trapezoid -> Trapezoid($)
    square -> Square($)
    rectangle -> Rectangle($)
    kite -> Kite($)
    """

    # square 2
    def repl_method(match):
        shape = match.group(1)  # 'rhombus'
        label = match.group(2)  # 1
        text = "[{}({})]".format(shape.capitalize(), label)
        return text

    pattern = re.compile(r'(quadrilateral|parallelogram|rhombus|trapezoid|square|rectangle|kite) (\d)')
    text = re.sub(pattern, repl_method, text)

    # rhombus
    def repl_method2(match):
        shape = match.group(2)  # 'rhombus'
        text = "[{}($)]".format(shape.capitalize())
        return text

    pattern2 = re.compile(r'(A | a |)(quadrilateral|parallelogram|rhombus|trapezoid|square|rectangle|kite)')
    text = re.sub(pattern2, repl_method2, text)

    return text


# [1.12]
def Match_Polygon(text):
    # polygon
    pattern = re.compile(r'(a |)([P|p]olygon)(?!\s[A-Z])(?=[\.\,\?\s])')
    target = r'[Polygon($)]'
    text = re.sub(pattern, target, text)

    return text


# [1.13]
def Match_Pentagon(text):
    """
    ABCDE -> Pentagon(A,B,C,D,E)
    Pentagon ABCDE -> Pentagon(A,B,C,D,E)
    """
    pattern = re.compile(
        r'(?:[P|p]olygon |)([P|p]entagon )?(?<![A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])(?![A-Z])(?=[\.\,\?\s])')
    target = r'[Pentagon(\2,\3,\4,\5,\6)]'
    text = re.sub(pattern, target, text)

    # a regular pentagon -> Pentagon($)
    pattern = re.compile(r'([p|P]entagon)(?=[\.\,\?\s])')
    target = r'[Pentagon($)]'
    text = re.sub(pattern, target, text)

    return text


# [1.14]
def Match_Hexagon(text):
    """
    ABCDEF -> Hexagon(A,B,C,D,E,F)
    Hexagon ABCDEF -> Hexagon(A,B,C,D,E,F)
    """
    pattern = re.compile(
        r'(?:[P|p]olygon |)([H|h]exagon )?(?<![A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])(?![A-Z])(?=[\.\,\?\s])')
    target = r'[Hexagon(\2,\3,\4,\5,\6,\7)]'
    text = re.sub(pattern, target, text)

    # a regular Hexagon -> Hexagon($)
    pattern = re.compile(r'([H|h]exagon)(?=[\.\,\?\s])')
    target = r'[Hexagon($)]'
    text = re.sub(pattern, target, text)

    return text


# [1.15]
def Match_Heptagon(text):
    """
    ABCDEFG -> Heptagon(A,B,C,D,E,F,G)
    Heptagon ABCDEFG -> Heptagon(A,B,C,D,E,F,G)
    """
    pattern = re.compile(
        r'(?:[P|p]olygon |)([H|h]eptagon )?(?<![A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])(?![A-Z])(?=[\.\,\?\s])')
    target = r'[Heptagon(\2,\3,\4,\5,\6,\7,\8)]'
    text = re.sub(pattern, target, text)

    # a regular Heptagon -> Heptagon($)
    pattern = re.compile(r'([H|h]eptagon)(?=[\.\,\?\s])')
    target = r'[Heptagon($)]'
    text = re.sub(pattern, target, text)

    return text


# [1.16]
def Match_Octagon(text):
    """
    ABCDEFGH -> Octagon(A,B,C,D,E,F,G,H)
    Octagon ABCDEFGH -> Octagon(A,B,C,D,E,F,G,H)
    """
    pattern = re.compile(
        r'(?:[P|p]olygon |)([O|o]ctagon )?(?<![A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])([A-Z])(?![A-Z])(?=[\.\,\?\s])')
    target = r'[Octagon(\2,\3,\4,\5,\6,\7,\8,\9)]'
    text = re.sub(pattern, target, text)

    # a regular Octagon -> Octagon($)
    pattern = re.compile(r'([O| o]ctagon)(?=[\.\,\?\s])')
    target = r'[Octagon($)]'
    text = re.sub(pattern, target, text)

    return text


# [1.17]
def Match_Circle(text):
    """
    odot K -> Circle(K)
    Circle O -> Circle(O)
    """
    pattern = re.compile(r'(\\odot|[C|c]ircle) ([A-Z])(?=[\.\,\?\s])')
    target = r'[Circle(\2)]'
    text = re.sub(pattern, target, text)

    # match example: Circles G, J, and K """
    pattern = re.compile(r'(?:[C|c]ircles|\\odot) ([A-Z]), ([A-Z]), (?:and )([A-Z])')
    target = r"[Circle(\1)], [Circle(\2)], [Circle(\3)]"
    text = re.sub(pattern, target, text)

    # In H,
    pattern = re.compile(r'(?:In| in) ([A-Z])(?=[\.\,\?\s])')
    target = r"In [Circle(\1)]"
    text = re.sub(pattern, target, text)

    # circle
    pattern = re.compile(r'(?:a |)[C|c]ircle(?=[\.\,\?\s])')
    target = r"[Circle($)]"
    text = re.sub(pattern, target, text)

    return text


# [1.18]
def Match_Arc(text):
    # widehat ACF -> Arc(A, C, F)
    pattern = re.compile(r'\\widehat ([A-Z])([A-Z])([A-Z])', re.IGNORECASE)
    target = r'[Arc(\1,\2,\3)]'
    text = re.sub(pattern, target, text)

    # widehat AB -> Arc(A, B)
    pattern = re.compile(r'\\widehat ([A-Z])([A-Z])', re.IGNORECASE)
    target = r'[Arc(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


# [1.19]
def Match_Sector(text):
    # sector -> Sector($)
    pattern = re.compile(r'(?<!\w)(?:a |)[S|s]ector(?!\s[A-Z])')
    target = r'[Sector($)]'
    text = re.sub(pattern, target, text)

    return text


# [1.20]
def Match_Shape(text):
    # region, shape, figure -> Sector($)
    pattern = re.compile(r'(a |)(region|shape|figure)(?:s|)(?!s)')
    target = r'[Shape($)]'
    text = re.sub(pattern, target, text)

    # "from W to W'."
    pattern = re.compile(r"from ([A-Z]) to ([A-Z])('|)")
    target = r'from [Shape(\1)] to [Shape(\2\3)]'
    text = re.sub(pattern, target, text)

    return text


##########################################
##### Unary Geometric Attributes (Level-2)
##########################################

# [2.1]
def Match_RightAngle(text):
    # If [Angle(R,S,T)] is right [Angle($)]
    pattern = re.compile(r'\[(Angle[\S]+)\] is right \[Angle\(\$\)\]')
    target = r'[RightAngle(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [2.2]
def Match_Right(text):
    # [Triangle(R,S,T)] is right [Triangle($)]
    pattern = re.compile(r'\[(Triangle[\S]+)\] is right \[Triangle\(\$\)\]')
    target = r'[Right(\1)]'
    text = re.sub(pattern, target, text)

    # hypotenuse of right [Triangle($)]
    pattern = re.compile(r'(?: a |)[R|r]ight \[(Triangle[\S]+)\]')
    target = r'[Right(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [2.3]
def Match_Isosceles(text):
    # [Triangle(R,S,T)] is isosceles
    pattern = re.compile(r'\[(\S+)\] is isosceles(?: \[Triangle\(\$\)\]|)')
    target = r'[Isosceles(\1)]'
    text = re.sub(pattern, target, text)

    # [Triangle(R,S,T)] and [Triangle(R,S,T)] are isosceles
    pattern = re.compile(r'\[(\S+)\] and \[(\S+)\] are isosceles')
    target = r'[Isosceles(\1)], [Isosceles(\2)]'
    text = re.sub(pattern, target, text)

    # Isosceles [Triangle(A,B,C)]
    pattern = re.compile(r'[I|i]sosceles? \[(\S+)\]')
    target = r'[Isosceles(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [2.4]
def Match_Equilateral(text):
    # [Triangle(F,G,H)] is equilateral
    pattern = re.compile(r'\[([\S]+)\] is equilateral')
    target = r'[Equilateral(\1)]'
    text = re.sub(pattern, target, text)

    # equilateral [Triangle(R,S,T)]
    pattern = re.compile(r'[E|e]quilateral \[([\S]+)\]')
    target = r'[Equilateral(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [2.5]
def Match_Regular(text):
    # [Polygon($)] is regular
    pattern = re.compile(r'\[([\S]+)\] is regular')
    target = r'[Regular(\1)]'
    text = re.sub(pattern, target, text)

    # regular [Polygon($)]
    pattern = re.compile(r'(?:[A|a] |)[R|r]egular \[([\S]+)\]')
    target = r'[Regular(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [2.6-2.9]
def Match_Color(text):
    colors = [r'red', r'blue', r'green', r'shaded']

    # shaded [Sector($)] -> [Shaded(Sector($))]
    for color in colors:
        pattern = re.compile(color + r' \[([\S]+)\](?=[\.\,\?\s])', re.IGNORECASE)
        Color = color[0].upper() + color[1:]
        target = r'[' + Color + r'(\1)]'
        text = re.sub(pattern, target, text)

    # blue to [Green(Shape($))]
    for color in colors:
        pattern = re.compile(color + r' to \[(Red|Blue|Green)\(([\S]+)\)\](?=[\.\,\?\s])', re.IGNORECASE)
        Color = color[0].upper() + color[1:]
        target = r'[' + Color + r'(\2)] to [\1(\2)]'
        text = re.sub(pattern, target, text)

    return text


##########################################
##### Geometric Attributes (Level-2)
##########################################

# [3.1]
def Match_AreaOf(text):
    # area of [Parallelogram(E,F,G,H)]
    pattern = re.compile(r'[A| a]rea of \[([\S]+)\]')
    target = r'[AreaOf(\1)]'
    text = re.sub(pattern, target, text)

    # find area.
    pattern = re.compile(r'(?<=[Ff]ind )area(?=[\s\,\.\?])')
    target = r'[AreaOf(Polygon($))]'
    text = re.sub(pattern, target, text)

    return text


# [3.2]
def Match_PerimeterOf(text):
    # perimeter of
    pattern = re.compile(r'[P| p]erimeter (?:or circumference |)of \[([\S]+)\]')
    target = r'[PerimeterOf(\1)]'
    text = re.sub(pattern, target, text)

    # a perimeter
    pattern = re.compile(r'(?:a |)perimeter(?=[\.\,\?\s])')
    target = r'[PerimeterOf(Polygon($))]'
    text = re.sub(pattern, target, text)

    return text


# [3.3]
def Match_RadiusOf(text):
    # radius of
    pattern = re.compile(r'(?<![\S])(?:radius of) \[([\S]+)\]')
    target = r'[RadiusOf(\1)]'
    text = re.sub(pattern, target, text)

    # In [Circle(P)], radius is 2
    pattern = re.compile(r'(?:In| in) \[Circle\((\S)\)\](?:,|) radius is ([\d]+)')
    target = r'[RadiusOf(Circle(\1))] is \2'
    text = re.sub(pattern, target, text)

    return text


# [3.4]
def Match_DiameterOf(text):
    # diameter of [Circle(Q)]
    pattern = re.compile(r'(?<! is )(?<! has )(?<!a )(?:diameter of) \[([\S]+)\]')
    target = r'[DiameterOf(\1)]'
    text = re.sub(pattern, target, text)

    # diameter is 18
    pattern = re.compile(r'diameter is ([\d]+)')
    target = r'[DiameterOf(Circle($))] is \1'
    text = re.sub(pattern, target, text)

    return text


# [3.5]
def Match_CircumferenceOf(text):
    # circumference of [], [] and []
    pattern = re.compile(r'(?<![\S])(?:circumference of) \[(\S+)\], \[(\S+)\](?:,) and \[(\S+)\]')
    target = r'[CircumferenceOf(\1)], [CircumferenceOf(\2)], and [CircumferenceOf(\3)]'
    text = re.sub(pattern, target, text)

    # circumference of
    pattern = re.compile(r'(?<![\S])(?:circumference of) \[(\S+)\]')
    target = r'[CircumferenceOf(\1)]'
    text = re.sub(pattern, target, text)

    # circumferences of three circles
    pattern = re.compile(r'circumference[s|] of three circles')
    target = r'[CircumferenceOf(Circle($1))], [CircumferenceOf(Circle($2))] and [CircumferenceOf(Circle($3))]'
    text = re.sub(pattern, target, text)

    # circumference of
    pattern = re.compile(r'(?<![\S])(?:circumference)(?=[\.\,\?\s])')
    target = r'[CircumferenceOf(Circle($))]'
    text = re.sub(pattern, target, text)

    return text


# [3.6]
def Match_AltitudeOf(text):
    # altitude of
    pattern = re.compile(r'(?<![\S])(?:altitude of) \[([\S]+)\]')
    target = r'[AltitudeOf(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [3.7]
def Match_HypotenuseOf(text):
    # hypotenuse of
    pattern = re.compile(r'(?<![\S])(?<!is |be )(?:hypotenuse of) \[([\S]+)\]')
    target = r'[HypotenuseOf(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [3.8]
def Match_SideOf(text):
    # side of
    pattern = re.compile(r'(?<![\S])(?:side of) \[(\S+)\]')
    target = r'[SideOf(\1)]'
    text = re.sub(pattern, target, text)

    # Find side length in [Isosceles(Triangle(D,E,F))].
    pattern = re.compile(r'(?<![\S])(?:side length in) \[(\S+)\]')
    target = r'[SideOf(\1)]'
    text = re.sub(pattern, target, text)

    # side is 1.
    pattern = re.compile(r'(?<![\S])(?:side)(?! measure)(?=[\.\,\?\s])')
    target = r'[SideOf(Regular(Polygon($)))]'
    text = re.sub(pattern, target, text)

    return text


# [3.9]
def Match_WidthOf(text):
    # width of [Square(A)]
    pattern = re.compile(r'(?<![\S])(?<!is |be )(?:width of) \[([\S]+)\]')
    target = r'[WidthOf(\1)]'
    text = re.sub(pattern, target, text)

    # width.
    pattern = re.compile(r'(?<![\S])(?<!is |be )width(?=[\.\,\?\s])')
    target = r'[WidthOf(Polygon($))]'
    text = re.sub(pattern, target, text)

    return text


# [3.10]
def Match_HeightOf(text):
    # height of [Triangle(A)]
    pattern = re.compile(r'(?<![\S])(?<!is |be )(?:height of) \[([\S]+)\]')
    target = r'[HeightOf(\1)]'
    text = re.sub(pattern, target, text)

    # height.
    pattern = re.compile(r'(?<![\S])(?<!is |be )height(?=[\.\,\?\s])')
    target = r'[HeightOf(Polygon($))]'
    text = re.sub(pattern, target, text)

    return text


# [3.11]
def Match_LegOf(text):
    # leg of
    pattern = re.compile(r'(?<![\S])(?<!is |be )(?:leg of) \[(\S+)\]')
    target = r'[LegOf(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [3.12]
def Match_BaseOf(text):
    # base of
    pattern = re.compile(r'(?<![\S])(?<!is |be )(?:base of) \[(\S+)\]')
    target = r'[BaseOf(\1)]'
    text = re.sub(pattern, target, text)

    # base.
    pattern = re.compile(r'(?<![\S])(?<!is |be )base(?=[\.\,\?\s])')
    target = r'[BaseOf(Polygon($))]'
    text = re.sub(pattern, target, text)

    return text


# [3.13]
def Match_MedianOf(text):
    # median of
    pattern = re.compile(r'(?<![\S])(?<!is |be )(?:median of) \[([\S]+)\]')
    target = r'[MedianOf(\1)]'
    text = re.sub(pattern, target, text)

    # median.
    pattern = re.compile(r'(?<![\S])(?<!is |be )median(?=[\.\,\?\s])')
    target = r'[MedianOf(Polygon($))]'
    text = re.sub(pattern, target, text)

    return text


# [3.14]
def Match_IntersectionOf(text):
    # pass
    return text


# [3.15]
def Match_MeasureOf(text):
    # measure of [Angle(T)] -> MeasureOf(Angle(T))
    pattern = re.compile(r'(?<![a-z])(?:m|measure of|angle measure of) \[Angle\((\S+)\)\]', flags=re.IGNORECASE)
    target = r'[MeasureOf(Angle(\1))]'
    text = re.sub(pattern, target, text)

    # measure of [Arc(A,B)] -> MeasureOf(Arc(A,B))
    pattern = re.compile(r'(?<![a-z])(?:m|measure of|angle measure of) \[Arc\((\S+)\)\]', flags=re.IGNORECASE)
    target = r'[MeasureOf(Arc(\1))]'
    text = re.sub(pattern, target, text)

    # measure of x
    pattern = re.compile(r'(?<![a-z])(?:m|measure of|angle measure of) ([a-zA-Z])(?=[\.\,\?\s])')
    target = r'[MeasureOf(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [3.16]
def Match_LengthOf(text):
    # length of [Arc(A,B)] -> LengthOf(Arc(A,B))
    pattern = re.compile(r'length of \[(\S+)\]')
    target = r'[LengthOf(\1)]'
    text = re.sub(pattern, target, text)

    # measure of [Line(A,B)] -> LengthOf(Line(A,B))
    pattern = re.compile(r'(?<=[\s|])(?:m|length of|measure of) \[(\S+)\]')
    target = r'[LengthOf(\1)]'
    text = re.sub(pattern, target, text)

    # [Line(A,B)] = 9
    pattern = re.compile(r'\[Line\((\S+)\)\](?= =)')
    target = r'[LengthOf(Line(\1))]'
    text = re.sub(pattern, target, text)

    # Find [Line(J,T)].
    pattern = re.compile(r'(?<=[F|f]ind )\[Line\((\S+)\)\]')
    target = r'[LengthOf(Line(\1))]'
    text = re.sub(pattern, target, text)

    return text


# [3.17]
def Match_ScaleFactorOf(text):
    # scale factor from [Shape(W)] to [Shape(W')]
    pattern = re.compile(r'scale (?:factor |)(?:of|from) \[(\S+)\] to \[(\S+)\]')
    target = r'[ScaleFactorOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # Find scale factor.
    pattern = re.compile(r'scale factor')
    target = r'[ScaleFactorOf(Shape($1),Shape($2))]'
    text = re.sub(pattern, target, text)

    return text


##########################################
##### Binary Geometric Relations (Level-2)
##########################################

# [4.1]
def Match_PointLiesOnLine(text):
    # [Line(Q,P)] and [Line(Q,R)] are opposite rays
    pattern = re.compile(r'\[Line\(([A-Z]),([A-Z])\)\] and \[Line\(([A-Z]),([A-Z])\)\] are opposite rays')
    target = r'[Line(\1,\2)], [Line(\3,\4)], [PointLiesOnLine(\1,Line(\2,\4))]'
    text = re.sub(pattern, target, text)

    return text


# [4.2]
def Match_PointLiesOnCircle(text):
    # Pass
    return text


# [4.3]
def Match_Parallel(text):
    """
    [Line(A,B)] \parallel [Line(C,D)]
    [Find(x)] so that [Line(m)] \parallel [Line(n)].
    """
    pattern = re.compile(r'\[([\S]+)\] (?:\\parallel|is parallel to) \[([\S]+)\](?=[\.\,\?\s]|$)')
    target = r'[Parallel(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


# [4.4]
def Match_Perpendicular(text):
    # [Line(A,D)] is perpendicular to [Line(B,C)]
    pattern = re.compile(r'\[([\S]+)\] (?:\\perp|is perpendicular to) \[([\S]+)\](?=[\.\,\?\s]|$)')
    target = r'[Perpendicular(\1,\2)]'
    text = re.sub(pattern, target, text)

    pattern = re.compile(r'\[(\S+)\] and \[(\S+)\] are perpendicular(?=[\.\,\?\s]|$)')
    target = r'[Perpendicular(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


# [4.5]
def Match_IntersectAt(text):
    # [Circle(G)], [Circle(J)] and [Circle(K)] intersect at L.
    pattern = re.compile(r'\[(\S+)\], \[(\S+)\] and \[(\S+)\] (?:intersect|meet) at (?:\[Point\(|)([A-Z])(?:\)\]|)')
    target = r'[IntersectAt(\1,\2,\3,Point(\4))]'
    text = re.sub(pattern, target, text)

    # l, m and n meet at T.
    pattern = re.compile(r'([a-z]), ([a-z]) and ([a-z]) (?:intersect|meet) at (?:\[Point\(|)([A-Z])(?:\)\]|)')
    target = r'[IntersectAt(Line(\1),Line(\2),Line(\3),Point(\4))]'
    text = re.sub(pattern, target, text)

    # [Line(B,D)] and [Line(A,C)] intersect at E.
    pattern = re.compile(r'\[(\S+)\] and \[(\S+)\] (?:intersect|meet) at (?:\[Point\(|)([A-Z])(?:\)\]|)')
    target = r'[IntersectAt(\1,\2,Point(\3))]'
    text = re.sub(pattern, target, text)

    # [Line(n)] intersects both l and m.
    pattern = re.compile(r'\[(\S+)\] intersects both ([a-z]) and ([a-z])(?=[\s\,\.\?])')
    target = r'[IntersectAt(\1,Line(\2),Point($))], [IntersectAt(\1,Line(\3),Point($))]'
    text = re.sub(pattern, target, text)

    return text


# [4.6]
def Match_BisectsAngle(text):
    # [Line(B,D)] bisects [Angle(A,B,F)]
    pattern = re.compile(r'\[(\S+)\] bisects \[(\S+)\]')
    target = r'[BisectsAngle(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(C,Q)] is angle bisector of [Angle(A,C,B)]
    pattern = re.compile(r'\[(\S+)\] is angle bisector of \[(\S+)\]')
    target = r'[BisectsAngle(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(C,Q)] is angle bisector.
    pattern = re.compile(r'\[(\S+)\] is angle bisector(?=[\s\,\.\?])')
    target = r'[BisectsAngle(\1,Angle($))]'
    text = re.sub(pattern, target, text)

    return text


# [4.7]
def Match_Congruent(text):
    # [Circle(A)] is congruent to [Circle(B)].
    pattern = re.compile(r'\[(\S+)\] (?:\\cong|is congruent to|is congruent) \[(\S+)\](?=[\s\,\.\?])')
    target = r'[Congruent(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


# [4.8]
def Match_Similar(text):
    """
    [XX] \sim [YY]. -> Similar(XX,YY))
    [XX] is similar to [YY]. -> Similar(XX,YY))
    """
    pattern = re.compile(r'\[([\S]+)\] (is similar to|\\sim) \[([\S]+)\](?=[\s\,\.\?])')
    target = r'[Similar(\1,\3)]'
    text = re.sub(pattern, target, text)

    # [XX] and [YY] are similar. -> Similar(XX,YY))
    pattern = re.compile(r'\[([\S]+)\] and \[([\S]+)\] are similar(?=[\s\,\.\?])')
    target = r'[Similar(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


# [4.9]
def Match_Tangent(text):
    # [Line(M,P)] is tangent to [Circle(O)]
    pattern = re.compile(r'\[(\S+)\] is tangent to \[(\S+)\](?=[\s\,\.\?])')
    target = r'[Tangent(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(M,P)] and [Line(N,P)] are tangent to [Circle(O)]
    pattern = re.compile(r'\[(\S+)\] and \[(\S+)\] are tangent to \[(\S+)\](?=[\s\,\.\?])')
    target = r'[Tangent(\1,\3)] [Tangent(\2, \3)]'
    text = re.sub(pattern, target, text)

    # Tangent [Line(M,P)] is drawn to [Circle(O)]
    pattern = re.compile(r'[T|t]angent \[(\S+)\] is drawn to \[(\S+)\](?=[\s\,\.\?])')
    target = r'[Tangent(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(A,E)] is tangent.
    pattern = re.compile(r'\[(\S+)\] is tangent(?=[\s\,\.\?])')
    target = r'[Tangent(\1,Circle($))]'
    text = re.sub(pattern, target, text)

    # segments appear tangent to circles are tangent
    pattern = re.compile(r'segments appear tangent to circles are tangent(?=[\s\,\.\?])')
    target = r'[Tangent(Line($),Circle($))]'
    text = re.sub(pattern, target, text)

    return text


# [4.10]
def Match_Secant(text):
    # pass
    return text


# [4.11]
def Match_CircumscribedTo(text):
    # [] is circumscribed about/to []
    pattern = re.compile(r'\[([\S]+)\] (?:is |be |)circumscribed (?:about|to) \[([\S]+)\](?=[\s\,\.\?])')
    target = r'[CircumscribedTo(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


# [4.12]
def Match_InscribedIn(text):
    # [] is inscribed in []
    pattern = re.compile(r'\[(\S+)\] (?:is |be |)inscribed (?:in|into) \[(\S+)\](?=[\s\,\.\?])')
    target = r'[InscribedIn(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


##########################################
##### A-IsXOf-B Geometric Relations (Level-2)
##########################################

# [5.1]
def Match_IsMidpointOf(text):
    # [Point(Q)] is midpoint of [Line(A,C)].
    pattern = re.compile(r'\[(\S+)\] (?:is|be) midpoint of \[(\S+)\]')
    target = r'[IsMidpointOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # P is midpoint of [Triangle(A,C,E)].
    pattern = re.compile(r'([A-Z]) (?:is|be) midpoint of \[([\S]+)\]')
    target = r'[IsMidpointOf(Point(\1),\2)]'
    text = re.sub(pattern, target, text)

    # [Point(Q)] is midpoint.
    pattern = re.compile(r'\[(\S+)\] (?:is|be) midpoint')
    target = r'[IsMidpointOf(\1,Line($))]'
    text = re.sub(pattern, target, text)

    # P is midpoint of [Triangle(A,C,E)].
    pattern = re.compile(r'([A-Z]) (?:is|be) midpoint')
    target = r'[IsMidpointOf(Point(\1),Line($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.2]
def Match_IsCentroidOf(text):
    # [Point(Q)] is centroid of [Triangle(A,C,E)].
    pattern = re.compile(r'\[(\S+)\] (?:is|be) (?:center|centroid) of \[(\S+)\]')
    target = r'[IsCentroidOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # P is centroid of [Triangle(A,C,E)].
    pattern = re.compile(r'([A-Z]) (?:is|be) (?:center|centroid) of \[([\S]+)\]')
    target = r'[IsCentroidOf(Point(\1),\2)]'
    text = re.sub(pattern, target, text)

    # [Point(Q)] is centroid.
    pattern = re.compile(r'\[(\S+)\] (?:is|be) (?:center|centroid)')
    target = r'[IsCentroidOf(\1,Shape($))]'
    text = re.sub(pattern, target, text)

    # P is centroid of [Triangle(A,C,E)].
    pattern = re.compile(r'([A-Z]) (?:is|be) (?:center|centroid)')
    target = r'[IsCentroidOf(Point(\1),Shape($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.3]
def Match_IsIncenterOf(text):
    # [Point(J)] is incenter of [Angle(A,B,C)].
    pattern = re.compile(r'\[(\S+)\] (?:is|be) incenter of \[Angle\((\S+)\)\]')
    target = r'[IsIncenterOf(\1,Triangle(\2))]'
    text = re.sub(pattern, target, text)

    # [Point(Q)] is incenter of [Triangle(A,C,E)].
    pattern = re.compile(r'\[(\S+)\] (?:is|be) incenter of \[(\S+)\]')
    target = r'[IsIncenterOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # P is incenter of [Triangle(A,C,E)].
    pattern = re.compile(r'([A-Z]) (?:is|be) incenter of \[(\S+)\]')
    target = r'[IsIncenterOf(Point(\1),\2)]'
    text = re.sub(pattern, target, text)

    # P is incenter.
    pattern = re.compile(r'([A-Z]) (?:is|be) incenter')
    target = r'[IsIncenterOf(Point(\1),Triangle($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.4]
def Match_IsRadiusOf(text):
    # [Line(C,D)] is radius of [Circle(C)] and
    pattern = re.compile(r'\[(\S+)\] (?:is|be) radius of \[(\S+)\]')
    target = r'[IsRadiusOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(A,B)] is radius.
    pattern = re.compile(r'\[(\S+)\] is radius(?=[\.\,\?\s])')
    target = r'[IsRadiusOf(\1,radius($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.5]
def Match_IsDiameterOf(text):
    # [Line(P,M)] is diameter of [Circle(R)]']
    pattern = re.compile(r'\[([\S]+)\] (?:is|be) diameter of \[([\S]+)\]')
    target = r'[IsDiameterOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(P,M)] is diameter.
    pattern = re.compile(r'\[([\S]+)\] (?:is|be) diameter')
    target = r'[IsDiameterOf(\1,Circle($))]'
    text = re.sub(pattern, target, text)

    # [Circle(A)] has diameter of [Line(D,F)]
    pattern = re.compile(r'\[([\S]+)\] has (?:a |)diameter (?:of |)\[([\S]+)\]')
    target = r'[IsDiameterOf(\2,\1)]'
    text = re.sub(pattern, target, text)

    return text


# [5.6]
def Match_IsMidsegmentOf(text):
    # [Line(C,D)] is midsegment of [Triangle(A,B,C)] and
    pattern = re.compile(r'\[(\S+)\] (?:is|be) midsegment of \[(\S+)\]')
    target = r'[IsMidsegmentOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(A,B)] is midsegment.
    pattern = re.compile(r'\[(\S+)\] is midsegment(?=[\.\,\?\s])')
    target = r'[IsMidsegmentOf(\1,Shape($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.7]
def Match_IsChordOf(text):
    # [Line(C,D)] is chord of [Circle(C)] and
    pattern = re.compile(r'\[(\S+)\] (?:is|be) chord of \[(\S+)\]')
    target = r'[IsChordOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(A,B)] is chord.
    pattern = re.compile(r'\[(\S+)\] is chord(?=[\.\,\?\s])')
    target = r'[IsChordOf(\1,Circle($))]'
    text = re.sub(pattern, target, text)

    # Chord AC
    pattern = re.compile(r'(?:[Cc]hord) \[(\S+)\](?=[\.\,\?\s])')
    target = r'[IsChordOf(\1,Circle($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.8]
def Match_IsSideOf(text):
    # [Line(C,D)] is side of [Triangle(A,B,C)] and
    pattern = re.compile(r'\[(\S+)\] (?:is|be) side of \[(\S+)\]')
    target = r'[IsSideOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(A,B)] is side.
    pattern = re.compile(r'\[(\S+)\] is side(?=[\.\,\?\s])')
    target = r'[IsSideOf(\1,Shape($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.9]
def Match_IsHypotenuseOf(text):
    # [Line(C,D)] is hypotenuse of [Triangle(A,B,C)]
    pattern = re.compile(r'\[(\S+)\] (?:is|be) hypotenuse of \[(\S+)\]')
    target = r'[IsHypotenuseOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(B,D)] is hypotenuse.
    pattern = re.compile(r'\[(\S+)\] is hypotenuse(?=[\.\,\?\s])')
    target = r'[IsHypotenuseOf(\1,Triangle($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.10]
def Match_IsPerpendicularBisectorOf(text):
    # [Line(A,B)] is perpendicular bisector of [Line(X,Z)]
    pattern = re.compile(r'\[(\S+)\] (?:is|be) perpendicular bisector of \[(\S+)\]')
    target = r'[IsPerpendicularBisectorOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # m is perpendicular bisector of [Line(X,Z)]
    pattern = re.compile(r'(?:[L|l]ine |)(?<![a-z])([a-z]) (?:is|be) perpendicular bisector of \[(\S+)\]')
    target = r'[IsPerpendicularBisectorOf(Line(\1),\2)]'
    text = re.sub(pattern, target, text)

    # [Line(A,B)] is perpendicular bisector
    pattern = re.compile(r'\[(\S+)\] (?:is|be) perpendicular bisector')
    target = r'[IsPerpendicularBisectorOf(\1,Line($))]'
    text = re.sub(pattern, target, text)

    # m is perpendicular bisector
    pattern = re.compile(r'(?:[L|l]ine |)(?<![a-z])([a-z]) (?:is|be) perpendicular bisector')
    target = r'[IsPerpendicularBisectorOf(Line(\1),Line($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.11]
def Match_IsAltitudeOf(text):
    # [Line(C,D)] is altitude of [Triangle(A,B,C)] and
    pattern = re.compile(r'\[(\S+)\] (?:is|be) altitude of \[(\S+)\]')
    target = r'[IsAltitudeOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(B,D)] is altitude.
    pattern = re.compile(r'\[(\S+)\] is altitude(?=[\.\,\?\s])')
    target = r'[IsAltitudeOf(\1,Shape($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.12]
def Match_IsMedianOf(text):
    # [Line(B,D)] is median of [Triangle(A,B,C)].
    pattern = re.compile(r'\[(\S+)\] (?:is|be) median of \[(\S+)\]')
    target = r'[IsMedianOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(B,D)] is median.
    pattern = re.compile(r'\[(\S+)\] is median')
    target = r'[IsMedianOf(\1,Shape($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.13]
def Match_IsBaseOf(text):
    # [Line(B,D)] is base of [Triangle(A,B,C)].
    pattern = re.compile(r'\[(\S+)\] (?:is|be) base of \[(\S+)\]')
    target = r'[IsBaseOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(B,D)] is base.
    pattern = re.compile(r'\[(\S+)\] is base(?=[\.\,\?\s])')
    target = r'[IsBaseOf(\1,Shape($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.14]
def Match_IsDiagonalOf(text):
    # [Line(A,C)] is diagonal of [Rhombus(A,B,C,D)]
    pattern = re.compile(r'\[(\S+)\] is diagonal of \[(\S+)\]')
    target = r'[IsDiagonalOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(A,C)] is diagonal.
    pattern = re.compile(r'\[(\S+)\] is diagonal(?=[\.\,\?\s])')
    target = r'[IsDiagonalOf(\1,Polygon($))]'
    text = re.sub(pattern, target, text)

    return text


# [5.15]
def Match_IsLegOf(text):
    # [Line(B,D)] is leg of [Triangle(A,B,C)].
    pattern = re.compile(r'\[(\S+)\] (?:is|be) leg of \[(\S+)\]')
    target = r'[IsLegOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(B,D)] is leg.
    pattern = re.compile(r'\[(\S+)\] is leg(?=[\.\,\?\s])')
    target = r'[IsLegOf(\1,Shape($))]'
    text = re.sub(pattern, target, text)

    return text


##########################################
##### Numerical Attributes and Relations (Level-2,3,N)
##########################################

# [6.1-6.4]
def Match_Trig(text):
    # matches all the trignometry functions
    trig_keys = [r'\\sin', r'\\cos', r'\\tan', r'\\cot']

    for trig in trig_keys:
        # \\sin a
        pattern = re.compile(trig + r' ([a-z])(?=[\.\,\?\s]|$)')
        new_trig = trig[2].upper() + trig[3:] + r'Of'
        text = re.sub(pattern, r'[' + new_trig + r'(\1)]', text)

        # \cos R => CosOf(Angle(R))  Because R implies Angle(R) here under the context of cos
        pattern = re.compile(trig + r' ([A-Z])(?=[\.\,\?\s]|$)')
        new_trig = trig[2].upper() + trig[3:] + r'Of'
        text = re.sub(pattern, r'[' + new_trig + r'(Angle(\1))]', text)

    return text


# [6.5]
def Match_HalfOf(text):
    # half
    pattern = re.compile(r'[Hh]alf \[([\S]+)\]')
    target = r'[HalfOf(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [6.6]
def Match_SquareOf(text):
    # square of
    pattern = re.compile(r'[S|s]quare of \[([\S]+)\]')
    target = r'[SquareOf(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [6.7]
def Match_SqrtOf(text):
    # pass
    return text


# [6.8]
def Match_RatioOf(text):
    # ratio of []
    pattern = re.compile(r'[R|r]atio of \[(\S+)\] to \[(\S+)\]')
    target = r'[RatioOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # ratio of []
    pattern = re.compile(r'[R|r]atio of \[(\S+)\]')
    target = r'[RatioOf(\1)]'
    text = re.sub(pattern, target, text)

    # \frac{[Line(I,J)]}{[Line(X,J)]
    pattern = re.compile(r'\\frac\{\[(\S+)\]\}\{\[(\S+)\]\}')
    target = r'[RatioOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


# [6.9]
def Match_SumOf(text):
    # sum of [CircumferenceOf(Circle(H))], [CircumferenceOf(Circle(J))] and [CircumferenceOf(Circle(K))]
    pattern = re.compile(r'sum of \[(\S+)\], \[(\S+)\] and \[(\S+)\]')
    target = r'[SumOf(\1,\2,\3)]'
    text = re.sub(pattern, target, text)

    # sum of [CircumferenceOf(Circle(H))], [Circle(J)] and [Circle(K)]
    pattern = re.compile(r'sum of \[(\S+)\] and \[(\S+)\]')
    target = r'[SumOf(\1,\2)]'
    text = re.sub(pattern, target, text)

    # sum of [CircumferenceOf(Circle(H))]
    pattern = re.compile(r'(?<![\S])sum of \[(\S+)\]')
    target = r'[SumOf((\1))]'
    text = re.sub(pattern, target, text)

    # [Angle(1)] and [Angle(2)] form a linear pair.
    pattern = re.compile(r'\[(\S+)\] and \[(\S+)\] form (?:a |)linear pair')
    target = r'[Equals(SumOf(MeasureOf(\1),MeasureOf(\1)),180)]'
    text = re.sub(pattern, target, text)

    # [Angle(1)] and [Angle(2)] form a linear pair.
    pattern = re.compile(r'\[(\S+)\] and \[(\S+)\] are complementary')
    target = r'[Equals(SumOf(MeasureOf(\1),MeasureOf(\1)),90)]'
    text = re.sub(pattern, target, text)

    return text


# [6.10]
def Match_AverageOf(text):
    # pass
    return text


# [6.11]
def Match_Add(text):
    # [HeightOf(Triangle($))] is 5 more than [BaseOf(Polygon($))]
    pattern = re.compile(r'(\[\S+\]) is (\d+) more than \[(\S+)\]')
    target = r'\1 is [Add(\3,\2)]'
    text = re.sub(pattern, target, text)

    # [Line(P,M)]+2
    pattern = re.compile(r'\[(\S+)\]\+(\d+)')
    target = r'[Add(\1,\2)]'
    text = re.sub(pattern, target, text)

    # 3+[Line(P,M)]
    pattern = re.compile(r'(\d+)\+\[(\S+)\]')
    target = r'[Add(\2,\1)]'
    text = re.sub(pattern, target, text)

    # [Line(P,M)]+[Line(K,P)]
    pattern = re.compile(r'\[(\S+)\]\+\[(\S+)\]')
    target = r'[Add(\1,\2)]'
    text = re.sub(pattern, target, text)

    return text


# [6.12]
def Match_Mul(text):
    numbers = {'twice ': '2', 'three times': '3', 'four times ': '4', 'five times ': '5', 'six times ': '6'}
    for word, number in numbers.items():
        pattern = re.compile(r'' + word)
        target = r'' + number
        text = re.sub(pattern, target, text)

    # [RadiusOf(Circle(A))] is 2[RadiusOf(Circle(B))] and 4[RadiusOf(Circle(C))]
    pattern = re.compile(r'(\[\S+\]) is (\d+)(\[\S+\]) and (\d+)(\[\S+\])')
    target = r'\1 is \2\3, \1 is \4\5'
    text = re.sub(pattern, target, text)

    # [Line(P,M)] = 2[Line(K,P)]
    pattern = re.compile(r'(\d+|\\frac{\S+}{\S+})(?:\s|)\[(\S+)\]')
    target = r'[Mul(\2,\1)]'
    text = re.sub(pattern, target, text)

    return text


# [6.13]
def Match_Sub(text):
    # pass
    return text


# [6.14]
def Match_Div(text):
    # pass
    return text


# [6.15]
def Match_Pow(text):
    # pass
    return text


# [6.16]
def Match_Equals(text):
    # Case1: [Line(A,B)] = [Line(B,C)]
    pattern = re.compile(r'\[(\S+)\] (?:=|is) \[(\S+)\](?=[\s\,\.\?])')
    target = r'[Equals(\1,\2)]'
    text = re.sub(pattern, target, text)

    # Case2: [XX] = 4x+10,
    """
    [XX] = 10a, -> Equals(XX, 10a)
    [MeasureOf(Angle(2))] = 2x,  -> 
    [MeasureOf(Angle(11))] = 4x+10, -> 
    [MeasureOf(Angle(D,G,F))] = 53 and 
    [MeasureOf(Arc(M,N))] = 98.5, so
    [MeasureOf(Angle(2))] = x+\\frac{10}{3}.
    """
    pattern = re.compile(r'\[(\S+)\] = (\S+)(?=[\s\,\.\?])')
    target = r'[Equals(\1,\2)]'
    text = re.sub(pattern, target, text)

    # Case3: [XX] is 4x+10,
    pattern = re.compile(r'\[(\S+)\] is (?![a-z]+[\.\,\?\s])(\S+)(?=[\s\,\.\?])')
    target = r'[Equals(\1,\2)]'
    text = re.sub(pattern, target, text)

    # Case4: a is 10.5
    pattern = re.compile(r'(?<![\S+])([a-z][\d]{0,2}) (?:=|is) (?![a-z]+[\.\,\?\s])(\S+)(?=[\.\,\?\s])')
    target = r'[Equals(\1,\2)]'
    text = re.sub(pattern, target, text)

    # Case5: A = 66.
    pattern = re.compile(r'([A-Z]) = (\d+)(?=[\.\,\?\s])')
    target = r'[Equals(AreaOf(Shape(\1)),\2)]'
    text = re.sub(pattern, target, text)

    # ,) -> )
    text = re.sub(r'[\,\.\?]+\)', ')', text)

    return text


# [6.17]
def Match_Find(text):
    # find x. -> Find(x)
    pattern = re.compile(r'([F|f]ind) ([a-z])(?=[\.\,\?\s]|$)')
    target = r'[Find(\2)]'
    text = re.sub(pattern, target, text)

    # Find [MeasureOf(Angle(T))]
    pattern = re.compile(r'([F|f]ind) \[([\S]+)\](?=[\.\,\?\s]|$)')
    target = r'[Find(\2)]'
    text = re.sub(pattern, target, text)

    # What is [MeasureOf(Angle(C))]?
    pattern = re.compile(r'(?:What is) \[([\S]+)\](?=[\.\,\?\s]|$)')
    target = r'[Find(\1)]'
    text = re.sub(pattern, target, text)

    return text


# [6.18]
def Match_UseTheorem(text):
    # According to Perpendicular Bisector Theorem
    pattern = re.compile(
        r'(?:[AUau]|)(?:ccording to |se |)([A-Z][a-z]{3,}) ([A-Z][a-z]{3,}) ([A-Z][a-z]{3,})(?=[\.\,\?\s])')
    target = r'[UseTheorem(\1_\2_\3)]'
    text = re.sub(pattern, target, text)

    # Pythagorean Triple
    pattern = re.compile(r'(?:[AUau]|)(?:ccording to |se |)([A-Z][a-z]{3,}) ([A-Z][a-z]{3,})(?=[\.\,\?\s])')
    target = r'[UseTheorem(\1_\2)]'
    text = re.sub(pattern, target, text)

    return text


##########################################
##### Simplify Logic Forms
##########################################

def Simplify_Logic_Form(text):
    # LengthOf(XXX) -> XXX
    pattern = re.compile(r'(?:LengthOf|MeasureOf)\((\S+?)\)')  # \S+?: shortest match
    target = r'\1'
    text = re.sub(pattern, target, text)

    return text


##########################################
##### Generate Logic Forms
##########################################

def generate_logic_forms(text):
    # Special Facts
    text = Match_Facts(text)

    # Split and reorganize the sentences
    text = Split_Shapes(text)  # [S1]

    # Geometry Shapes(L-1)
    text = Match_Point(text)  # [1.1]
    text = Match_Line(text)  # [1.2]
    text = Match_Angle(text)  # [1.3]
    text = Match_Triangle(text)  # [1.4]
    text = Match_Quadrilateral(text)  # [1.5-1.11]
    text = Match_Polygon(text)  # [1.12]
    text = Match_Pentagon(text)  # [1.13]
    text = Match_Hexagon(text)  # [1.14]
    text = Match_Heptagon(text)  # [1.15]
    text = Match_Octagon(text)  # [1.16]
    text = Match_Circle(text)  # [1.17]
    text = Match_Arc(text)  # [1.18]
    text = Match_Sector(text)  # [1.19]
    text = Match_Shape(text)  # [1.20]

    # Unary Geometric Attributes(L-2)
    text = Match_RightAngle(text)  # [2.1]
    text = Match_Right(text)  # [2.2]
    text = Match_Isosceles(text)  # [2.3]
    text = Match_Equilateral(text)  # [2.4]
    text = Match_Regular(text)  # [2.5]
    text = Match_Color(text)  # [2.6-2.9]

    # Split and reorganize the sentences
    text = Split_Shape_Has_Of(text)  # [S2.1]
    text = Split_In_A_B_Is_C(text)  # [S2.2]
    text = Split_Eqs_ABC(text)  # [S2.3]
    text = Split_Shapes_ABC(text)  # [S2.4]
    text = Split_Shapes_AB(text)  # [S2.5]
    text = Split_Specials(text)  # [S2.6]

    # Geometry Attributes(L-2,3)
    text = Match_AreaOf(text)  # [3.1]
    text = Match_PerimeterOf(text)  # [3.2]
    text = Match_RadiusOf(text)  # [3.3]
    text = Match_DiameterOf(text)  # [3.4]
    text = Match_CircumferenceOf(text)  # [3.5]
    text = Match_AltitudeOf(text)  # [3.6]
    text = Match_HypotenuseOf(text)  # [3.7]
    text = Match_SideOf(text)  # [3.8]
    text = Match_WidthOf(text)  # [3.9]
    text = Match_HeightOf(text)  # [3.10]
    text = Match_LegOf(text)  # [3.11]
    text = Match_BaseOf(text)  # [3.12]
    text = Match_MedianOf(text)  # [3.13]
    text = Match_IntersectionOf(text)  # [3.14]
    text = Match_MeasureOf(text)  # [3.15]
    text = Match_LengthOf(text)  # [3.16]
    text = Match_ScaleFactorOf(text)  # [3.17]

    # Binary Geometric Relations(L-2,3)
    text = Match_PointLiesOnLine(text)  # [4.1]
    text = Match_PointLiesOnCircle(text)  # [4.2]
    text = Match_Parallel(text)  # [4.3]
    text = Match_Perpendicular(text)  # [4.4]
    text = Match_IntersectAt(text)  # [4.5]
    text = Match_BisectsAngle(text)  # [4.6]
    text = Match_Congruent(text)  # [4.7]
    text = Match_Similar(text)  # [4.8]
    text = Match_Tangent(text)  # [4.9]
    text = Match_Secant(text)  # [4.10]
    text = Match_CircumscribedTo(text)  # [4.11]
    text = Match_InscribedIn(text)  # [4.12]

    # A-IsXOf-B  Geometric Relations(L-2,3)
    text = Match_IsMidpointOf(text)  # [5.1]
    text = Match_IsCentroidOf(text)  # [5.2]
    text = Match_IsIncenterOf(text)  # [5.3]
    text = Match_IsRadiusOf(text)  # [5.4]
    text = Match_IsDiameterOf(text)  # [5.5]
    text = Match_IsMidsegmentOf(text)  # [5.6]
    text = Match_IsChordOf(text)  # [5.7]
    text = Match_IsSideOf(text)  # [5.8]
    text = Match_IsHypotenuseOf(text)  # [5.9]
    text = Match_IsPerpendicularBisectorOf(text)  # [5.10]
    text = Match_IsAltitudeOf(text)  # [5.11]
    text = Match_IsMedianOf(text)  # [5.12]
    text = Match_IsBaseOf(text)  # [5.13]
    text = Match_IsDiagonalOf(text)  # [5.14]
    text = Match_IsLegOf(text)  # [5.15]

    # Numerical Attributes and Relations(L-3,N)
    text = Match_Trig(text)  # [6.1-6.4]
    text = Match_HalfOf(text)  # [6.5]
    text = Match_SquareOf(text)  # [6.6]
    text = Match_SqrtOf(text)  # [6.7]
    text = Match_RatioOf(text)  # [6.8]
    text = Match_SumOf(text)  # [6.9]
    text = Match_AverageOf(text)  # [6.10]
    text = Match_Add(text)  # [6.11]
    text = Match_Mul(text)  # [6.12]
    text = Match_Sub(text)  # [6.13]
    text = Match_Div(text)  # [6.14]
    text = Match_Pow(text)  # [6.15]
    text = Match_Equals(text)  # [6.16]
    text = Match_Find(text)  # [6.17]
    text = Match_UseTheorem(text)  # [6.18]

    return text


##########################################
##### Extract and Analyse Logic Forms
##########################################

def extract_logic_forms(text):
    # extract logic forms in processed text
    logic_forms = re.findall(r'\[.+?\]', text)
    logic_forms = [ele.replace('[', '').replace(']', '') for ele in logic_forms]

    # delete repeated logic forms
    logic_forms = list(dict.fromkeys(logic_forms))

    # move Find(x) to the end of the list
    find_index = [i for i, s in enumerate(logic_forms) if 'Find' in s]
    if len(find_index) > 0:
        idx = find_index[0]
        find_ele = logic_forms.pop(idx)
        logic_forms.append(find_ele)

    return logic_forms


def reduce_logic_text(text):
    """
    remove all existing logic forms in text
    text = "In rhombus ABCD, [LengthOf(Line(A, B), 2x+3)] and [LengthOf(Line(B, C), 5x)]. [Find(x)]."
    reduced_text = In rhombus ABCD,  and . .
    """
    # remove [exp]
    text = " " + text
    text = re.sub(r'\[.+?\]', "", text)  # non-greedy mode，shorter matched text is better

    # ignore nonsense words
    nonsense = ['\.', '\,', '\?', '\s\s']
    nonsense += [' in ', ' if ', ' so ', ' to ', ' is ']
    nonsense += [' and ', ' use ', ' for ', ' let ']
    nonsense += [' with ', ' that ', 'unit', 'then']
    nonsense += ['given', 'assume', 'number', 'inscribed', 'necessary', 'centimeter']
    nonsense += ['if necessary', ' formed by ', 'consisting of']
    nonsense += ['Round| to nearest whole number', 'Round| nearest \w+( of \w+|)', '(side|angle) measure',
                 'whole number', 'degree']
    nonsense += ['Which of following statements about is true']
    nonsense += ['Which of following facts would be sufficient prove']
    nonsense += ['Hint: Draw auxiliary line']
    nonsense += ['which cannot be true']
    nonsense += ['lengths of bases of']

    for word in nonsense:
        pattern = re.compile(word, re.IGNORECASE)
        text = pattern.sub(" ", text)

    text = re.sub(r'[\s]+', r' ', text)
    text = text.strip()

    return text


def is_valid(logic_forms):
    is_valid = True
    for logic_form in logic_forms:
        ln = len(re.findall(r"\(", logic_form))
        rn = len(re.findall(r"\)", logic_form))
        if ln != rn or "((" in logic_form or "])" in logic_form:
            print(logic_form)
            is_valid = False

    return is_valid


def is_success(text):
    """
    A very simple metric.
    """
    # check if logic_forms are valid
    valid = is_valid(logic_forms)

    if valid and len(text) < 4:
        return True
    return False


def parse(text):
    # remove nonsense words in problem text
    simplified_text = simplify_text(text)

    # generate logic forms
    output_text = generate_logic_forms(simplified_text)  # replaced with logic forms

    # extract logic forms from problem text
    logic_forms = extract_logic_forms(output_text)  # extract logic forms: ['', '']

    # reduce text
    reduced_text = reduce_logic_text(output_text)

    return logic_forms, output_text, reduced_text


##########################################
##### Main Function
##########################################

if __name__ == "__main__":

    DATA_PATH = '../data/geometry3k'
    OUTPUT_FILE = 'text_logic_forms.json'

    output_data = {}
    count_success = 0
    count = 0

    print("Paring the problem text into logic forms...")
    for pid in range(3002):
        # data splits
        if pid in range(2101):
            split = 'train'
        elif pid in range(2101, 2401):
            split = 'val'
        else:
            split = 'test'

        # whole problem text and annotated logic forms
        with open(os.path.join(DATA_PATH, split, str(pid), 'data.json'), 'r') as f:
            data = json.load(f)
        assert str(pid) == str(data['id']) # prob id: 0-3001
        text = data['compact_text']

        # extract logic forms from problem text
        logic_forms, output_text, reduced_text = parse(text)

        # determine if the text is successfully parsed
        success = is_success(reduced_text)
        if success:
            count_success += 1

        # save output data
        output_data[pid] = {}
        output_data[pid]["text_logic_forms"] = logic_forms
        output_data[pid]["output_text"] = output_text
        output_data[pid]["success"] = success

    # save the results
    estimated_acc = count_success/3002*100
    print("Successfully parsed rate = {:.2f}%".format(estimated_acc))

    print("Saving results to {}".format(OUTPUT_FILE))
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent = 2, separators=(',', ': '))

