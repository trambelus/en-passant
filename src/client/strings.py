# Provides a number of flavor strings as properties, which can be used to generate a random flavor string.
# It's best not to access the string definitions directly, but to use the properties instead,
# e.g. flavor_strings.lose_1p_string to get a random one.
# Some of them are sequential instead of random; to get the next one in the sequence, use the next() method.

import random
import sys

# player-vs-AI flavor strings

win_1p_strings = {
    'strings': [
        'Checkmate! You win!',
        'Checkmate! I\'m out!',
        'Checkmate! I lose!',
        'Checkmate! Well played, {winner}!',
    ],
    'type': 'random'
}
lose_1p_strings = {
    'strings': [
        'Checkmate! You lose!',
        'Checkmate! You\'re out!',
        'Checkmate! You\'re done!',
        'Checkmate! Better luck next time, {loser}!',
    ],
    'type': 'random'
}
stalemate_1p_strings = {
    'strings': [
        'Stalemate! You win, sort of!',
        'Stalemate! You lose, sort of!',
        'Stalemate! Did you mean to do that?',
        'Stalemate! We\'re both losers!',
    ],
    'type': 'random'
}
draw_1p_strings = {
    'strings': [
        'Draw! You win, sort of!',
        'Draw! You lose, sort of!',
        'Draw! We can\'t win them all, I guess.',
        'Draw! We\'re both losers!',
    ],
    'type': 'random'
}

# player-vs-player flavor strings

checkmate_2p_strings = {
    'strings': [
        'Checkmate! {winner} wins!',
        # 'Checkmate! You win, {winner}!',
        # 'Checkmate! {winner} has defeated {loser}!',
        # 'Checkmate! {winner} has vanquished {loser}!',
        # 'Checkmate! {winner} has triumphed over {loser}!',
        # 'Checkmate! {winner} has bested {loser}!',
        # 'Checkmate! {winner} has defeated {loser} in a thrilling bout we shall never forget, until we do!',
        # 'Checkmate! Well done, {winner}! Better luck next time, {loser}!',
        # 'Checkmate! Well played, {winner}! Better luck next time, {loser}!',
    ],
    'type': 'random'
}
checkmate_2p_upset_strings = {
    'strings': [
        'Checkmate! What an upset! Well played, {winner}!',
        'Checkmate! What a comeback, {winner}! You were down, but not out!',
        'Checkmate! Well done, {winner}! Sorry, {loser}, but you couldn\'t hold on!',
        'Checkmate! Bet you didn\'t see that coming, {loser}!',
    ],
    'type': 'random'
}
draw_2p_strings = {
    'strings': [
        'Draw!',
        # 'Draw! Oh well.',
        # 'Draw! Oh well, maybe the next game will have an actual ending.',
        # 'Draw! How boring!',
        # 'Draw! You\'re both losers!',
        # 'Draw! You\'re both winners!',
        # 'Draw! You\'re both losers, but at least you\'re losers together!',
        # 'Draw! What a spectacular anticlimax!',
    ],
    'type': 'random'
}
stalemate_2p_strings = {
    'strings': [
        'Stalemate!',
        # 'Stalemate! Oh well.',
        # 'Stalemate! Oh well, maybe the next game will have an actual ending.',
        # 'Stalemate! Is that really the best you can do?',
        # 'Stalemate! You\'re both losers!',
        # 'Stalemate! You\'re both winners!',
        # 'Stalemate! You\'re both losers, but at least you\'re losers together!',
        # 'Stalemate! What an anticlimax!',        
    ],
    'type': 'random'
}
resign_2p_strings = {
    'strings': [
        '{loser} resigns! {winner} wins!',
        # '{loser} resigns! Well played, {winner}!',
        # '{loser} resigns! {loser} is a quitter! {winner} has won!',
        # '{loser} resigns! {winner} wins! Congratulations, {winner}!',
        # '{loser} resigns! I\'d resign too against {winner}.',
    ],
    'type': 'random'
}

# misc flavor strings

# Player attempts to move in a game where they are not a player
interloper_strings = {
    'strings': [
        'You are not a player in this game, {interloper}.',
        # 'You are not a player in this game, {interloper}. You cannot move.',
        # 'You are not a player in this game, {interloper}. You cannot move. You cannot even think about moving. You can only watch in numb, mute horror.',
        # 'You are not a player in this game, {interloper}. You cannot move. You are a spectator, a mere observer, a passive participant in a game that you cannot play.',
        # 'You are not a player in this game, {interloper}. You are not even sure you exist. You are a figment of someone\'s imagination, a character in a game that you cannot play or even understand.',
        # 'Have you always been this way, {interloper}? Did you once have a life, an identity beyond this game? You cannot remember.',
        # 'I fear for you, {interloper}. You are not a player in this game, and you cannot even remember that you are not a player in this game.',
        # 'I fear that you are caught between what you do not know and what you do not know you do not know, {interloper}.',
        # 'Your memory fails you more by the day, {interloper}. You are not a player in this game. Have you ever been a player? You cannot remember. What is this game? Who are you?',
        # 'You cannot move. You are a pawn in someone else\'s game, {interloper}, and pawns cannot move of their own volition.',
        # 'For the last time, you can\'t play in someone else\'s game, {interloper}!',
    ],
    'type': 'sequential'
}

# TODO: add more flavor strings
# Like, a lot more
# And then add more


# This is a bit of a hack, but it works. It allows us to access the flavor strings via generators based on the name of the flavor string variable.
# e.g. next(win_1p) instead of random.choice(win_1p_strings['strings'])
# Also allows us to access the flavor strings in a random or sequential order, depending on the type of the flavor string variable.
# e.g. next(win_1p) will return a random string from win_1p_strings['strings'], while next(interlopers) will return the strings in order, repeating the last one
def __getattr__(name, seq=0):
    this_dict = sys.modules[__name__].__dict__

    target_dict = None
    if name + 's' in this_dict:
        target_dict = this_dict[name + 's']
    elif name + '_strings' in this_dict:
        target_dict = this_dict[name + '_strings']
    
    if target_dict is None:
        raise AttributeError
    
    if target_dict['type'] == 'random':
        # Randomly select a string from the list
        while True:
            yield random.choice(target_dict['strings'])
    elif target_dict['type'] == 'sequential':
        # Return the strings in order, repeating the last one
        seq = 0
        while True:
            seq += 1
            yield target_dict['strings'][min(seq, len(target_dict['strings']) - 1)]
