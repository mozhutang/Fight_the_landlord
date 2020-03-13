from board import GameBoardData
from input_parser import InputParser
import farmer_agents
import landlord_agents
from constants import *
import random


class demo(object):

    @staticmethod
    def start_game(farmer_agent, landlord_agent, farmer_policy, landlord_policy, f, landlord_depth=None, farmer_depth=None):
        print('***GAME START***')
        board_state = GameBoardData()
        LandlordAgents = getattr(landlord_agents, landlord_agent)
        FarmerAgents = getattr(farmer_agents, farmer_agent)
        landlord = LandlordAgents(LANDLORD, landlord_policy, depth=landlord_depth)
        farmer_one = FarmerAgents(FARMER_ONE, farmer_policy, depth=farmer_depth)
        farmer_two = FarmerAgents(FARMER_TWO, farmer_policy, depth=farmer_depth)
        while not board_state.is_terminal:
            turn = board_state.turn
            action = None
            if turn == FARMER_ONE:
                action = farmer_one.get_action(board_state)
                print('farmer1 plays {0}'.format(action))
            if turn == FARMER_TWO:
                action = farmer_two.get_action(board_state)
                print('farmer2 plays {0}'.format(action))
            if turn == LANDLORD:
                action = landlord.get_action(board_state)
                print('landlord plays {0}'.format(action))
            board_state = board_state.next_state(action)
        print('*** GAME OVER, {0} WIN ***'.format(board_state.winner))
        winner = 'landlord'
        if board_state.winner in [FARMER_ONE, FARMER_TWO]:
            winner = 'farmer'
        f.write('[landlord]{0}-{1}-{2}::[farmer]{3}-{4}-{5}::[winner]{6}||\n'.format(landlord_agent,
                                                                                landlord_policy,
                                                                                landlord_depth,
                                                                                farmer_agent,
                                                                                farmer_policy,
                                                                                farmer_depth,
                                                                                winner))


if __name__ == '__main__':
    f = open('minimax.txt', 'a')
    for i in range(0, 30):
        demo.start_game(ALPHA_BETA_AGENT, ALPHA_BETA_AGENT, EVALUATION, EVALUATION, f, landlord_depth=3,
                                 farmer_depth=3)
    f.close()
    print ('minimax done')

