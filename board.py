from constants import *
import random
from collections import Counter
import itertools
import sys
import inspect


class BoardData(object):
    def __init__(self, prev_data=None):
        if prev_data is not None:
            self.base_card = prev_data.base_card  # the card landlord holds
            self.discarded_card = prev_data.discarded_card  # discarded cards
            self.previous_play = prev_data.previous_play
            self.agent_order = prev_data.agent_order
            self.turn = prev_data.turn
            self.pass_count = prev_data.pass_count
            self.card_combinations = prev_data.card_combinations
            self.is_terminal = prev_data.is_terminal
            self.winner = prev_data.winner
            self.hands = prev_data.hands
            self.combos = prev_data.combos
        else:
            self.base_card = []  # the card landlord holds
            self.discarded_card = []  # discarded cards
            self.previous_play = (PASS, [])
            farmer_order = random.sample([FARMER_ONE, FARMER_TWO], 2)
            self.agent_order = [LANDLORD] + farmer_order
            self.turn = LANDLORD
            self.pass_count = 0
            self.card_combinations = CardCombinations()
            self.is_terminal = False
            self.winner = None
            base_card, pile_one, pile_two, pile_three = deal()
            self.hands = {
                LANDLORD: base_card + pile_one,
                FARMER_ONE: pile_two,
                FARMER_TWO: pile_three,
            }
            self.combos = {
                LANDLORD: Hand.get_all_combos(self.hands[LANDLORD]),
                FARMER_ONE: Hand.get_all_combos(self.hands[FARMER_ONE]),
                FARMER_TWO: Hand.get_all_combos(self.hands[FARMER_TWO]),
            }

    def copy(self, BoardClass):
        state = BoardClass(self)
        state.base_card = self.base_card
        state.discarded_card = self.discarded_card
        state.previous_play = self.previous_play
        state.agent_order = self.agent_order
        state.turn = self.turn
        state.pass_count = self.pass_count
        state.is_terminal = self.is_terminal
        state.winner = self.winner
        state.hands = self.hands.copy()
        self.combos = self.combos.copy()
        return state

    @property
    def agent_order_pretty(self):
        pretty_order = []
        for o in self.agent_order:
            if o == FARMER_ONE:
                pretty_order.append('farmer1')
            if o == FARMER_TWO:
                pretty_order.append('farmer2')
            if o == LANDLORD:
                pretty_order.append('landlord')
        return pretty_order

    def get_next_player(self):
        current_turn_index = self.agent_order.index(self.turn)
        return self.agent_order[(current_turn_index + 1) % 3]

    def get_hands(self, agent_id):
        return self.hands[agent_id]

    def is_win(self, agent_id):
        if agent_id == FARMER_ONE or agent_id == FARMER_TWO:
            is_win = self.is_terminal and \
                     (len(self.get_hands(FARMER_ONE)) == 0 or
                      len(self.get_hands(FARMER_TWO)) == 0)
            return is_win
        else:
            return self.is_terminal and len(self.get_hands(LANDLORD)) == 0

    def is_loose(self, agent_id):
        if agent_id == LANDLORD:
            return self.is_terminal and len(self.get_hands(LANDLORD)) > 0
        else:
            return self.is_terminal and len(self.get_hands(FARMER_ONE)) > 0 and len(self.get_hands(FARMER_TWO)) > 0

    def get_position(self, agent_id):
        pos = self.agent_order.index(agent_id)
        return pos

    """
    make sure the hash are the same if the state is the same
    """
    def formalize(self, agent_id):
        return tuple(sorted(self.hands[agent_id]))
        # return tuple(sorted(self.hands[LANDLORD])), \
        #        tuple(sorted(self.hands[FARMER_ONE])), \
        #        tuple(sorted(self.hands[FARMER_TWO]))


class GameBoardData(BoardData):
    def next_state(self, action):
        next_state = self.copy(GameBoardData)
        play_type, card_list = action
        card_left = Counter(self.get_hands(self.turn)) - Counter(card_list)
        if len(card_left) == 0:
            next_state.is_terminal = True
            next_state.winner = self.turn
        if play_type == PASS and self.pass_count < 1:
            next_state.pass_count += 1
            next_state.turn = self.get_next_player()
            return next_state
        if play_type != PASS:
            next_state.pass_count = 0
        next_state.previous_play = (play_type, card_list)
        next_state.hands[self.turn] = list(card_left.elements())
        next_state.turn = self.get_next_player()
        next_state.discarded_card = self.discarded_card + list(card_list)
        return next_state

    def get_actions(self, agent_id=None):
        if self.is_terminal:
            return []
        if agent_id is None:
            agent_id = self.turn
        current_hand = self.get_hands(agent_id)
        actions = Hand.get_successors(self.previous_play, current_hand, self.combos[agent_id])
        return actions


class NonDeterministicBoardData(BoardData):
    def next_state(self, action):
        pass

    def get_actions(self, agent_id):
        pass

class Hand(object):

    @staticmethod
    def get_successors(previous_play, current_hand, all_combos):
        """
        :return: a list of tuple (prev_play_type, prev_card_list)
        """
        prev_play_type, prev_card_list = previous_play
        if all_combos is not None:
            current_hand = Counter(current_hand)
            successors = []
            for combo_type, combo in all_combos:
                intersection = (Counter(combo) & Counter(current_hand)).elements()
                if len(list(intersection)) == len(list(combo)):
                    if prev_play_type == PASS:
                        successors.append((combo_type, combo))
                    elif combo_type == BOMB:
                        if prev_play_type == BOMB:
                            if combo[0] > prev_card_list[0]:
                                successors.append((combo_type, combo))
                        elif prev_play_type != KING_BOMB:
                            successors.append((combo_type, combo))
                    elif combo_type == KING_BOMB:
                        successors.append((combo_type, combo))
                    elif combo_type == prev_play_type and combo[0] > prev_card_list[0] and \
                            len(list(combo)) == len(prev_card_list):
                        successors.append((combo_type, combo))
            successors.append((PASS, ()))
            if prev_play_type == PASS:
                successors = [s for s in successors if s != (PASS, ())]
            return successors

    @staticmethod
    def get_all_combos(initial_hand):
        current_hand = Counter(initial_hand)
        successors = []
        for combo_type, combo_list in card_combinations.items():
            for combo in combo_list:
                intersection = (Counter(combo) & Counter(current_hand)).elements()
                if len(list(intersection)) == len(combo):
                    successors.append((combo_type, combo))
        successors.append((PASS, ()))
        return successors

    @staticmethod
    def get_combo_type(previous_play, card_input, combos):
        if card_input == PASS:
            return PASS, ()
        successors = Hand.get_successors(previous_play, card_input, combos)
        for successor_type, successor_list in successors:
            if len(successor_list) == len(card_input):
                return successor_type, card_input
        raise ValueError('Invalid Play')


class CardCombinations(object):

    def __init__(self):
        self._single = set()
        self._pair = set()
        self._trio = set()
        self._chain = set()
        self._pairs_chain = set()
        self._trio_single = set()
        self._trio_pair = set()
        self._airplane = set()
        self._airplane_small = set()
        self._airplane_large = set()
        self._four_with_two = set()
        self._four_with_pairs = set()
        self._bomb = set()
        self._king_bomb = set()
        self._card_types = [THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, J, Q, K, A, TWO, BLACK_JOKER, RED_JOKER]
        self._card_types_for_chain = [THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, J, Q, K, A]
        self.get_all_combinations()

    def __iter__(self):
        yield from {
            SINGLE: self._single,
            PAIR: self._pair,
            TRIO: self._trio,
            CHAIN: self._chain,
            PAIRS_CHAIN: self._pairs_chain,
            TRIO_SINGLE: self._trio_single,
            TRIO_PAIR: self._trio_pair,
            AIRPLANE: self._airplane,
            AIRPLANE_SMALL: self._airplane_small,
            AIRPLANE_LARGE: self._airplane_large,
            FOUR_WITH_TWO: self._four_with_two,
            FOUR_WITH_PAIRS: self._four_with_pairs,
            BOMB: self._bomb,
            KING_BOMB: self._king_bomb
        }.items()

    def get_all_combinations(self):
        for c in self._card_types:
            self._single.add((c,))
            if c < BLACK_JOKER:
                self._pair.add((c,) * 2)
                self._trio.add((c,) * 3)
                self._bomb.add((c,) * 4)
        self._king_bomb.add((BLACK_JOKER, RED_JOKER))
        # chain
        for i in range(0, len(self._card_types_for_chain)):
            for j in range(i + 5, len(self._card_types_for_chain)):
                self._chain.add(tuple(self._card_types_for_chain[i:j]))
        # pairs chain
        for i in range(0, len(self._card_types_for_chain)):
            for j in range(i + 3, len(self._card_types_for_chain)):
                sorted_list = sorted(self._card_types_for_chain[i:j] * 2)
                self._pairs_chain.add(tuple(sorted_list))
        # trio with single card
        for t in self._trio:
            for c in self._card_types:
                if t[0] != c:
                    self._trio_single.add(t + (c,))
        # trio with pairs
        for t in self._trio:
            for p in self._pair:
                if t[0] != p[0]:
                    self._trio_pair.add(t + p)
        # four with two cards
        two_cards_combinations = itertools.combinations(self._card_types, 2)
        for b in self._bomb:
            for c in two_cards_combinations:
                if b[0] != c[0] and b[0] != c[1]:
                    self._four_with_two.add(b + c)
        # bomb with pairs
        for b in self._bomb:
            for p in self._pair:
                if b[0] != p[0]:
                    self._four_with_pairs.add(b + p)

        # airplane combos
        for i in range(0, len(self._card_types_for_chain)):
            for j in range(i + 2, len(self._card_types_for_chain)):
                sorted_list = sorted(self._card_types_for_chain[i:j] * 3)
                tuple_sorted_list = tuple(sorted_list)
                # airplane
                if len(sorted_list) <= 20:
                    self._airplane.add(tuple_sorted_list)
                # airplane with small wings
                if len(sorted_list) + (j - i) <= 20:
                    for c in itertools.combinations(self._card_types, j - i):
                        if len(set(c).intersection(tuple_sorted_list)) == 0:
                            self._airplane_small.add(tuple_sorted_list + c)
                # airplane with large wings
                if len(sorted_list) + (j - i) * 2 <= 20:
                    for c in itertools.combinations(self._card_types, j - i):
                        if len(set(c).intersection(tuple_sorted_list)) == 0:
                            self._airplane_large.add(tuple_sorted_list + c * 2)


card_combinations = dict(CardCombinations())


def raise_not_defined():
    file_name = inspect.stack()[1][1]
    line = inspect.stack()[1][2]
    method = inspect.stack()[1][3]

    print("*** Method not implemented: %s at line %s of %s" % (method, line, file_name))
    sys.exit(1)


def deal():
    deck_without_joker = [THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, J, Q, K, A, TWO] * 4
    deck = deck_without_joker + [BLACK_JOKER, RED_JOKER]
    random.shuffle(deck)
    # create three public cards for landlord
    base_card = deck[0:3]
    # deal deck into 17 cards
    pile_one = deck[3: 20]
    pile_two = deck[20: 37]
    pile_three = deck[37: 54]
    return base_card, pile_one, pile_two, pile_three


class Agents:
    def __init__(self, agent_id, evaluation=RANDOM):
        self.agent_id = agent_id
        self.evaluation = evaluation

    def get_action(self, board):
        raise_not_defined()


class MultiAgentSearch(Agents):
    def __init__(self, agent_id, max_depth=10):
        Agents.__init__(self, agent_id)
        self.max_depth = max_depth

    def evaluate(self, board, evaluation):
        if board.is_win(self.agent_id):
            return 1000
        if board.is_loose(self.agent_id):
            return -1000
        hand = board.get_hands(self.agent_id)
        if evaluation == EVALUATION:
            return sum(card_rating[c] for c in hand) + 24 - len(hand)

    def is_terminal(self, depth, board):
        return board.is_terminal or depth >= self.max_depth


class ManualAgent(Agents):
    def __init__(self, card_list, evaluation):
        Agents.__init__(self, card_list, evaluation)

    def get_action(self, board):
        while True:
            print('Your hand:')
            sorted_hand = sorted(board.get_hands(board.turn))
            # sorted_hand_pretty = [card_pretty_name[name] for name in sorted_hand]
            print(sorted_hand)
            result = input('What are you going to play?\n')
            try:
                card_list = result.split(',')
                if card_list[0] == 'PASS':
                    combo_type = 'PASS'
                    play = ()
                    return combo_type, play
                else:
                    card_list_int = list(map(int, card_list))
                    play = tuple(card_list_int)
                    action = Hand.get_combo_type(board.previous_play, play, board.combos[self.agent_id])
                return action
            except Exception as e:
                print('Invalid input or play, please try again.')
