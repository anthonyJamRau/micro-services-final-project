import random
from flask import Flask, jsonify, request
from helper_card import playingCard
import itertools

app = Flask(__name__)

class blackJackSim:
    def __init__(self,shoe_size):
        self.count = 0

        # simple hi lo strategy
        self.point_values = {
            '2': 1, '3': 1, '4': 1, '5': 1, '6': 1,
            '7': 0, '8': 0, '9': 0,
            '10': -1, 'J': -1, 'Q': -1, 'K': -1, 'A': -1
        }

        self.card_nums = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] 
        self.card_types = ['hearts','diamonds','clubs','spades']

        self.shoe = list(itertools.product(self.card_nums,self.card_types))*shoe_size

        # on each creation of the shoe, shuffle
        random.shuffle(self.shoe)

    def dealCard(self):
        if not self.shoe:
            return None, "Shoe is empty"
        
        card = self.shoe.pop()

        self.count += self.point_values[card[0]]

        return card
    
    def getCurrentCount(self):
        return self.count
    
@app.route('/deal',methods = ['GET'])
def deal():
    card = simulator.dealCard()
    pretty_card = playingCard(rank = card[0], suit = card[1]).prettyReturn()
    return jsonify({
        'message':'Card dealt successfully',
        'current_count':simulator.getCurrentCount(),
        'card_dealt':f'{pretty_card}'
    })

@app.route('/reset',methods = ['POST']):
    simulator.__init__()
    return jsonify({
        'message' : 'Shoe and count reset successfully'
    })

if __name__ == "__main__":
    simulator = blackJackSim(shoe_size=5)
    app.run(debug=True)
