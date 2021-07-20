# Predicate Definitions


##  1. Geometric Shapes (20)


|  #   | Predicates      |  Level   | Logic form templates                                         | Comments       |
| :--: | --------------- | :--: | ------------------------------------------------------------ | -------------- |
|  1  | `Point`         |  1   | `Point(A)`, `Point($)`                                       |                |
|  2  | `Line`          |  1   | `Line(A,B)`, `Line(m)`, `Line($)`                            |                |
|  3  | `Angle`         |  1   | `Angle(A,B,C)`, `Angle(A)`, `Angle(1)`, ` Angle($)`          |                |
|  4  | `Triangle`      |  1   | `Triangle(A,B,C)`, `Triangle($)`, `Triangle($1,$2,$3)`       |                |
|  5  | `Quadrilateral` |  1   | `Quadrilateral(A,B,C,D)`, `Quadrilateral($)`                 |          |
|  6  | `Parallelogram` |  1   | `Parallelogram(A,B,C,D)`, `Parallelogram(1)`, `Parallelogram($)` |      |
|  7  | `Square`        |  1   | `Square(A,B,C,D)`, `Square(1)`, `Square($)`                  |          |
|  8  | `Rectangle`     |  1   | `Rectangle(A,B,C,D)`, `Rectangle(1)`, `Rectangle($)`         |            |
|  9  | `Rhombus`       |  1   | `Rhombus(A,B,C,D)`, `Rhombus(1)`, `Rhombus($)`               |            |
| 10  | `Trapezoid`     |  1   | `Trapezoid(A,B,C,D)`, `Trapezoid(1)`, `Trapezoid($)`         |            |
| 11  | `Kite`          |  1   | `Kite(A,B,C,D)`, `Kite(1)`, `Kite($)`                        |            |
| 12  | `Polygon`       |  1   | `Polygon($)`                                                 |          |
| 13  | `Pentagon`      |  1   | `Pentagon(A,B,C,D,E)`, `Pentagon($)`                         |          |
| 14  | `Hexagon`       |  1   | `Hexagon(A,B,C,D,E,F)`, `Hexagon($)`                         |          |
| 15  | `Heptagon`      |  1   | `Heptagon(A,B,C,D,E,F,G)`, `Heptagon($)`                     |          |
| 16  | `Octagon`       |  1   | `Octagon(A,B,C,D,E,F,G,H)`, `Octagon($)`                     |          |
| 17  | `Circle`        |  1   | `Circle(A)`, `Circle(1)`, `Circle($)`                        |            |
| 18  | `Arc`           |  1   | `Arc(A,B)`, `Arc(A,B,C)`, `Arc($)`                           |            |
| 19  | `Sector`        |  1   | `Sector(O,A,B)`, `Sector($)`                                 |            |
| 20  | `Shape`         |  1   | `Shape($)`                                                   | Unknown shapes or regions |



##  2. Unary Geometric Attributes (9)

| #    | Predicates    |  Level   | Logic form templates      | Comments       |
| ---- | ------------- | :--: | ------------------------- | -------------- |
| 1   | `RightAngle`  |  2   | `RightAngle(Angle($))`    |            |
| 2   | `Right`       |  2   | `Right(Triangle($))`      | Right triangle |
| 3   | `Isosceles`   |  2   | `Isosceles(Polygon($))`   | Isosceles polygon |
| 4   | `Equilateral` |  2   | `Equilateral(Polygon($))` | Equilateral polygon |
| 5   | `Regular`     |  2   | `Regular(Polygon($))`     |    |
| 6   | `Red`         |  2   | `Red(Shape($))`           |            |
| 7   | `Blue`        |  2   | `Blue(Shape($))`          |           |
| 8   | `Green`       |  2   | `Green(Shape($))`         |            |
| 9   | `Shaded`      |  2   | `Shaded(Shape($))`        |            |



## 3. Geometric Attributes (17)

-   Here `[A-Z]` stands for logic form of the prior level (e.g. level 1 logic forms - Shapes)

| #    | Predicates        |  Level   | Logic form templates  | Comments           |
| ---- | ----------------- | :--: | --------------------- | ------------------ |
| 1   | `AreaOf`          | 2,3  | `AreaOf(A)`           |          |
| 2   | `PerimeterOf`     | 2,3  | `PerimeterOf(A)`      | Perimeter of the polygon A      |
| 3   | `RadiusOf`        | 2,3  | `RadiusOf(A)`         |                |
| 4   | `DiameterOf`      | 2,3  | `DiameterOf(A)`       |                |
| 5   | `CircumferenceOf` | 2,3  | `CircumferenceOf(A)`  | Perimeter of the circle A         |
| 6   | `AltitudeOf`      | 2,3  | `AltitudeOf(A)`       | Altitude of the polygon A         |
| 7   | `HypotenuseOf`    | 2,3  | `HypotenuseOf(A)`     | Hypotenuse of the triangle A       |
| 8   | `SideOf`          | 2,3  | `SideOf(A)`           | Side of the square A       |
| 9   | `WidthOf`         | 2,3  | `WidthOf(A)`          | Width of the quadrilateral A         |
| 10  | `HeightOf`        | 2,3  | `HeightOf(A)`         | Height of the quadrilateral A         |
| 11  | `LegOf`           | 2,3  | `LegOf(A)`            | Leg of the trapezoid A         |
| 12  | `BaseOf`          | 2,3  | `BaseOf(A)`           | Base of the polygon A       |
| 13  | `MedianOf`        | 2,3  | `MedianOf(A)`         | Median of the polygon A     |
| 14   | `IntersectionOf`  | 2,3  | `IntersectionOf(A,B)` | Intersection of shapes A and B     |
| 15  | `MeasureOf`       | 2,3  | `MeasureOf(A)`        | Measure of the angle A               |
| 16  | `LengthOf`        | 2,3  | `LengthOf(A)`         | Length of the line A               |
| 17  | `ScaleFactorOf`   | 2,3  | `ScaleFactorOf(A,B)`  | Scale factor of the shape A to the shape B  |




##  4. Binary Geometric Relations (12)

| #    | Predicates          |  Level   | Logic form templates                               | Comments   |
| ---- | ------------------- | :--: | -------------------------------------------------- | ---------- |
| 1   | `PointLiesOnLine`   | 2,3  | `PointLiesOnLine(Point($),Line($1,$2)/LegOf(...))` |    |
| 2    | `PointLiesOnCircle` | 2,3  | `PointLiesOnCircle(Point($),Circle($))`            |    |
| 3   | `Parallel`          | 2,3  | `Parallel(Line($),Line($))`                        |        |
| 4   | `Perpendicular`     | 2,3  | `Perpendicular(Line($),Line($))`                   |        |
| 5   | `IntersectAt`       | 2,3  | `IntersectAt(Line($),Line($),Line($),Point($))`    |      |
| 6   | `BisectsAngle`      | 2,3  | `BisectsAngle(Line($),Angle($))`                   |      |
| 7   | `Congruent`         | 2,3  | `Congruent(Polygon($),Polygon($))`                 |        |
| 8   | `Similar`           | 2,3  | `Similar(Polygon($),Polygon($))`                   |        |
| 9   | `Tangent`           | 2,3  | `Tangent(Line($),Circle($))`                       | |
| 10   | `Secant`            | 2,3  | `Secant(Line($),Circle($))`                        | |
| 11  | `CircumscribedTo`   | 2,3  | `CircumscribedTo(Shape($),Shape($))`               |      |
| 12  | `InscribedIn`       | 2,3  | `InscribedIn(Shape($),Shape($))`                   |      |



##  5. A-IsXOf-B  Geometric Relations (15)

| #    | Predicates                  |  Level   | Logic form templates                             | Comments                       |
| ---- | --------------------------- | :--: | ------------------------------------------------ | ------------------------------ |
| 1   | `IsMidpointOf`              | 2,3  | `IsMidpointOf(Point($),Line($))`                 | Point A is the midpoint of line B                |
| 2   | `IsCentroidOf`              | 2,3  | `IsCentroidOf(Point($),Shape($))`                | Point A is the centroid of shape B |
| 3   | `IsIncenterOf`              | 2,3  | `IsIncenterOf(Point($),Shape($))`                | Point A is the incenter of shape B |
| 4   | `IsRadiusOf`                | 2,3  | `IsRadiusOf(Line($),Circle($))`                  | Line A is the radius of circle B                 |
| 5   | `IsDiameterOf`              | 2,3  | `IsDiameterOf(Line($),Circle($))`                | Line A is the diameter of circle B                 |
| 6   | `IsMidsegmentOf`            | 2,3  | `IsMidsegmentOf(Line($),Triangle($))`            | Line A is the midsegment of triangle B           |
| 7   | `IsChordOf`                 | 2,3  | `IsChordOf(Line($),Circle($))`                   | Line A is the chord of circle B                   |
| 8   | `IsSideOf`                  | 2,3  | `IsSideOf(Line($),Polygon($))`                   | Line A is the side of polygon B               |
| 9   | `IsHypotenuseOf`            | 2,3  | `IsHypotenuseOf(Line($),Triangle($))`            | Line A is the hypotenuse of triangle B             |
| 10  | `IsPerpendicularBisectorOf` | 2,3  | `IsPerpendicularBisectorOf(Line($),Triangle($))` | Line A is the perpendicular bisector of triangle B      |
| 11  | `IsAltitudeOf`              | 2,3  | `IsAltitudeOf(Line($),Triangle($))`              | Line A is the altitude of triangle B             |
| 12  | `IsMedianOf`                | 2,3  | `IsMedianOf(Line($),Quadrilateral($))`           | Line A is the median of quadrilateral B         |
| 13  | `IsBaseOf`                  | 2,3  | `IsBaseOf(Line($),Quadrilateral($))`             | Line A is the base of quadrilateral B             |
| 14  | `IsDiagonalOf`              | 2,3  | `IsDiagonalOf(Line($),Quadrilateral($))`         | Line A is the diagonal of quadrilateral B           |
| 15  | `IsLegOf`                   | 2,3  | `IsLegOf(Line($),Trapezoid($))`                  | Line A is the leg of trapezoid B             |



##  6. Numerical Attributes and Relations (18)

| #    | Predicates   |  Level   | Logic form templates                 | Comments |
| ---- | ------------ | :--: | ------------------------------------ | -------- |
| 1   | `SinOf`      | 1,2  | `SinOf(Var)`                         |      |
| 2   | `CosOf`      | 1,2  | `CosOf(Var)`                         |      |
| 3   | `TanOf`      | 1,2  | `TanOf(Var)`                         |      |
| 4   | `CotOf`      | 1,2  | `CotOf(Var)`                         |      |
| 5   | `HalfOf`     | 1,2  | `HalfOf(Var)`                        |      |
| 6   | `SquareOf`   | 1,2  | `SquareOf(Var)`                      |      |
| 7    | `SqrtOf`     | 1,2  | `SqrtOf(Var)`                        |      |
| 8   | `RatioOf`    | 2,3  | `RatioOf(Var)`, `RatioOf(Var1,Var2)` |      |
| 9   | `SumOf`      | 2,3  | `SumOf(Var1,Var2,...)`               |       |
| 10   | `AverageOf`  | 2,3  | `AverageOf(Var1,Var2,...)`           |      |
| 11  | `Add`        | 2,3  | `Add(Var1,Var2,...)`                 |        |
| 12  | `Mul`        | 2,3  | `Mul(Var1,Var2,...)`                 |        |
| 13   | `Sub`        | 2,3  | `Sub(Var1,Var2,...)`                 |        |
| 14   | `Div`        | 2,3  | `Div(Var1,Var2,...)`                 |        |
| 15   | `Pow`        | 2,3  | `Pow(Var1,Var2)`                     |        |
| 16  | `Equals`     | 2,3  | `Equals(Var1,Var2)`                  |      |
| 17  | `Find`       | 2,3  | `Find(Var)`                          | Find the value of the varible     |
| 18  | `UseTheorem` |  N   | `UseTheorem(A_B_C)`                  |  |



