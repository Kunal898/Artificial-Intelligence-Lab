Prolog is a programming language used in Artificial Intelligence. It is based on logic and rules.

In Prolog, a program is written using facts, rules, and queries.

Facts are statements that represent information that is true.
Example:

parent(premlal, kunal).

Rules define relationships between facts.
Example:

father(X, Y) :- parent(X, Y), male(X).

Queries are questions asked to the program to get answers.
Example:

?- father(X, kunal).

Prolog uses two important concepts:

Unification – matching variables with values.

Backtracking – trying another solution if the first one fails.

In this practical, a family relationship system is created. Family members are defined using facts and relationships like father, mother, sibling, son, and daughter are defined using rules.

The program can be executed using SWI-Prolog, which is a popular Prolog environment. This helps us understand how logic programming and relationships are represented in Artificial Intelligence.
