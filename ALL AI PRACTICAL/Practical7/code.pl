parent(premlal, kunal). 
parent(chetna, kunal).
parent(premlal, akanksha).
parent(chetna, akanksha).
male(premlal).
male(kunal).
female(chetna). 
female(akanksha).
wife(chetna, premlal).
husband(premlal, chetna).
father(X, Y) :parent(X, Y), 
male(X).
mother(X, Y) :parent(X, Y),
female(X).
child(X, Y) :parent(Y, X).
son(X, Y) :child(X, Y),
male(X).
daughter(X, Y) :child(X, Y), 
female(X). 
sibling(X, Y) :parent(Z, X),
parent(Z, Y),
X \= Y.

