# Tests for game_session.py

from game_session import tokenize_move

# For each key in the second dict, if the key is present in the first dict, assert that the values are equal
def assert_contains(dict1, dict2):
    for key in dict2:
        if key in dict1:
            assert dict1[key] == dict2[key]

def test_tokenize_move():
    assert_contains(tokenize_move('e4'), {'piece': 'P', 'to_rank': 'e', 'to_file': '4'})
    assert_contains(tokenize_move('Nf3'), {'piece': 'N', 'to_rank': 'f', 'to_file': '3'})
    assert_contains(tokenize_move('Bb5'), {'piece': 'B', 'to_rank': 'b', 'to_file': '5'})
    assert_contains(tokenize_move('Ra6'), {'piece': 'R', 'to_rank': 'a', 'to_file': '6'})
    assert_contains(tokenize_move('Qd8+'), {'piece': 'Q', 'to_rank': 'd', 'to_file': '8', 'check': '+'})
    assert_contains(tokenize_move('Kxf1'), {'piece': 'K', 'to_rank': 'f', 'to_file': '1', 'capture': 'x'})
    assert_contains(tokenize_move('a8q'), {'piece': 'P', 'to_rank': 'a', 'to_file': '8', 'promotion': 'Q'})
    assert_contains(tokenize_move('a8=Q'), {'piece': 'P', 'to_rank': 'a', 'to_file': '8', 'promotion': 'Q'})
    assert_contains(tokenize_move('a8/Q'), {'piece': 'P', 'to_rank': 'a', 'to_file': '8', 'promotion': 'Q'})
    assert_contains(tokenize_move('e3d4'), {'piece': None, 'from_rank': 'e', 'from_file': '3', 'to_rank': 'd', 'to_file': '4'})
    assert_contains(tokenize_move('e3xd4'), {'piece': 'P', 'from_rank': 'e', 'from_file': '3', 'to_rank': 'd', 'to_file': '4', 'capture': 'x'})
    assert_contains(tokenize_move('Qhe1'), {'piece': 'Q', 'from_rank': 'h', 'to_rank': 'e', 'to_file': '1'})
    assert_contains(tokenize_move('Q4e1'), {'piece': 'Q', 'from_file': '4', 'to_rank': 'e', 'to_file': '1'})
    assert_contains(tokenize_move('Qh4e1'), {'piece': 'Q', 'from_rank': 'h', 'from_file': '4', 'to_rank': 'e', 'to_file': '1'})
    assert_contains(tokenize_move('Qh4xe1#'), {'piece': 'Q', 'from_rank': 'h', 'from_file': '4', 'to_rank': 'e', 'to_file': '1', 'capture': 'x', 'check': '#'})
    assert_contains(tokenize_move('a8a8'), {'piece': None, 'from_rank': 'a', 'from_file': '8', 'to_rank': 'a', 'to_file': '8'})
    assert_contains(tokenize_move('Qa8a8'), {'piece': 'Q', 'from_rank': 'a', 'from_file': '8', 'to_rank': 'a', 'to_file': '8'})
    # Tests that should fail
    assert tokenize_move('a7a') == {}
    assert tokenize_move('a77') == {}
    assert tokenize_move('Qh44xd4') == {}
    assert tokenize_move('Qh4xd4d') == {}
    assert tokenize_move('a8=') == {}
