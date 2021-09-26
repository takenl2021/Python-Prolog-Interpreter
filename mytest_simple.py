from prologpy.solver import Solver

def test_simple_goal_query():

    rules_text = """
        brother_sister(joe, monica).
        brother_sister(eric, erica).
        brother_sister(jim, rebecca).
    """

    goal_text = """
        brother_sister(jim, rebecca).
    """

    solver = Solver(rules_text)
    solution = solver.find_solutions(goal_text)

    return solution

def test_multi_variable_solutions():

    rules_text = """
        is_tall(jack, yes).
        is_tall(eric, no).
        is_tall(johnny, yes).
        is_tall(mark, no).
    """

    query_text = """
        is_tall(Y, yes)
    """

    solver = Solver(rules_text)
    solutions = solver.find_solutions(query_text)

    assert len(solutions.get("Y")) == 2

    assert ("jack" in str(solution) for solution in solutions.get("Y"))
    assert ("johnny" in str(solution) for solution in solutions.get("Y"))


def test_find_bad_dog():

    rules_text = """
        bad_dog(Dog) :-
           bites(Dog, Person),
           is_person(Person),
           is_dog(Dog).

        bites(fido, postman).
        is_person(postman).
        is_dog(fido).
    """

    query_text = """
        bad_dog( X )
    """

    solver = Solver(rules_text)
    solutions = solver.find_solutions(query_text)

    assert len(solutions.get("X")) == 1

    assert ("fido" in str(solution) for solution in solutions.get("X"))


def test_rule_sub():

    rules_text = """

        親escendant(X, Y) :- offspring(X, Y).
        親escendant(X, Z) :- offspring(X, Y), 親escendant(Y, Z).
        
        offspring(abraham, hanako).
        offspring(abraham, 与作).
        offspring(issac, esau).
        offspring(与作, ヤコブ６０).

    """

    query_text = """

        親escendant(与作, _人間).

    """

    solver = Solver(rules_text)
    solutions = solver.find_solutions(query_text)

    return solutions.get("_人間")
   

if __name__ == '__main__':
    #1つ目の質問
    ans = test_simple_goal_query()
    print("1つめの質問の回答=",ans)

    #2つ目の質問
    ans2 = test_rule_sub();
    print ("2つめ", ans2)
    for ans_ele in ans2:
        print(ans_ele)