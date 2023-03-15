# Tests for game_session.py

import json

from game_session import tokenize_move, GameSession

# For each key in the second dict, if the key is present in the first dict, assert that the values are equal
def assert_contains(dict1, dict2):
    for key in dict2:
        if key in dict1:
            assert dict1[key] == dict2[key]

# Asserts that two lists of strings are equal
def assert_list_equal(list1, list2):
    assert len(list1) == len(list2)
    for i in range(len(list1)):
        assert list1[i] == list2[i]

# Assert that two dicts are equal
def assert_dict_equal(dict1, dict2):
    assert len(dict1) == len(dict2)
    for key in dict1:
        assert key in dict2
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

def test_serialize_game_session():
    game_session = GameSession(moves=['e4', 'e5', 'Qh5', 'Nc6', 'Bc4', 'Nf6'],
                               fen='r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
                               game_options={ 'variant': 'standard', 'chess960_pos': -1, 'time_limit': -1, 'time_increment': 0 },
                               session_id='test_session_id')
    game_session_loaded = GameSession.from_json(game_session.to_json())
    assert_list_equal(game_session_loaded.moves, game_session.moves)
    assert game_session_loaded.fen == game_session.fen
    assert_dict_equal(game_session_loaded.game_options, game_session.game_options)
    assert game_session_loaded.session_id == game_session.session_id

test_serialize_game_session()