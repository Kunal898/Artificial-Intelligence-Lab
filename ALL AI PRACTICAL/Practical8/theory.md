THEORY:
Semantic Network
A semantic network is a graphical knowledge representation technique consisting of:
 Nodes → Concepts / Objects
 Edges→ Relationships
Common relations:
 ISA → Inheritance
 HAS-A → Property
 CAN → Ability
It is closely related to predicate logic representation, where:
isa(dog, animal).
has(dog, tail).
can(bird, fly).
Relationship to Predicate Logic
A semantic network can be represented using first-order predicates:
Semantic Relation Predicate Form
Dog is an Animal isa(dog, animal)
Bird can Fly can(bird, fly)
Dog has Tail has(dog, tail)

Artificial Intelligence Lab (N-PCCCS601P)

Department of CSE

Inheritance rule:
If
isa(X, Y) and has(Y, Z)
Then
has(X, Z)
Semantic Network Example
Nodes:
 Animal
 Bird
 Dog
 Sparrow
Relationships:
 Bird ISA Animal
 Dog ISA Animal
 Sparrow ISA Bird
 Animal has cells
 Bird can fly
 Dog can bark
