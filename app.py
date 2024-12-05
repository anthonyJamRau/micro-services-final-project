import random
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from helper_card import playingCard
import itertools
from dotenv import load_dotenv
import os
from policy_definition import return_policy
import pandas as pd

load_dotenv()
app = Flask(__name__)

client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
app.secret_key = os.getenv('secret_key')
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

blueprint = make_google_blueprint(
    client_id=client_id,
    client_secret=client_secret,
    scope=["profile", "email"],
    offline=True,
    reprompt_consent=False
)
app.register_blueprint(blueprint, url_prefix="/login")

class blackJackSim:
    def __init__(self,shoe_size):
        self.count = 0
        self.true_count = 0
        self.minimum_bet = 5
        self.user_balance = 1000
        self.double_bet = False

        # simple hi lo strategy
        self.point_values = {
            '2': 1, '3': 1, '4': 1, '5': 1, '6': 1,
            '7': 0, '8': 0, '9': 0,
            '10': -1, 'J': -1, 'Q': -1, 'K': -1, 'A': -1
        }

        self.card_nums = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] 
        self.card_types = ['hearts','diamonds','clubs','spades']

        self.shoe = list(itertools.product(self.card_nums,self.card_types))*shoe_size
        self.starting_shoe_cards = len(self.shoe)
        self.shoe_size = shoe_size

        # on each creation of the shoe, shuffle
        random.shuffle(self.shoe)

        self.user_hand = []
        self.dealer_hand = []
        self.policy = return_policy()



    def dealCard(self, burn = False):
        if not self.shoe:
            return None, "Shoe is empty"
        
        card = self.shoe.pop()

        if not burn:
            self.count += self.point_values[card[0]]
            self.true_count = round(self.count/round(self.shoe_size*(len(self.shoe)/self.starting_shoe_cards)))

        return card
    

    def startHand(self):
        self.user_hand = []
        self.dealer_hand = []
        self.user_hand.append(self.dealCard())
        self.dealer_hand.append(self.dealCard())
        self.user_hand.append(self.dealCard())

        return self.user_hand, self.dealer_hand


    def calculateHandValue(self, hand):
        hand_value = 0
        aces = 0
        for card in hand:
            rank = card[0]
            if rank in ['J','Q','K']:
                hand_value += 10
            elif rank == 'A':
                hand_value += 11
                aces += 1 
            else:
                hand_value += int(rank)

        while hand_value > 21 and aces:
            hand_value -= 10
            aces -= 1

        return hand_value
    
    def userHit(self):
        card = self.dealCard()
        self.user_hand.append(card)
        return card
    
    def dealerHit(self):
        card = self.dealCard()
        self.dealer_hand.append(card)
        return card
    
    def resolve_bets(self,outcome):
        if outcome == 'win':
            if self.double_bet:
                print('here')
                self.user_balance += self.minimum_bet*4
            else:
                print('here')
                self.user_balance += self.minimum_bet*2
        elif outcome == 'tie':
            self.user_balance += self.minimum_bet
        self.double_bet = False
        return

    def get_balance(self):
        return self.user_balance
    
    def getCurrentCount(self):
        return self.count
    
    def getTrueCount(self):
        return self.true_count
    
    def getShoeSize(self):
        return len(self.shoe)

    def getStartingShoeSize(self):
        return self.starting_shoe_cards
    
    def getUserHand(self):
        return self.user_hand
    
    def getDealerHand(self):
        return self.dealer_hand
    
    def getPolicy(self):
        return self.policy.to_html(classes='table table-striped',index=True)

    def get_minbet(self):
        return self.minimum_bet
    
    
@app.route("/")
def index():
    google_data = None
    user_info_endpoint = '/oauth2/v2/userinfo'
    if google.authorized:
        try:
            google_data = google.get(user_info_endpoint).json()
        except:
            return redirect(url_for("google.login"))
    return render_template('index_v3.j2', google_data=google_data)

@app.route('/login')
def login():
    return redirect(url_for('google.login'))


@app.route('/deal', methods=['GET'])
def deal():
    card = simulator.dealCard()
    if card:
        pretty_card_html = playingCard(rank=card[0], suit=card[1]).prettyReturn()
        return jsonify({
            'message': 'Card dealt successfully',
            'current_count': simulator.getCurrentCount(),
            'card_dealt': pretty_card_html
        })
    else:
        return jsonify({
            'message': 'No cards left in the shoe',
            'current_count': simulator.getCurrentCount()
        })

@app.route('/reset',methods = ['POST'])
def reset():
    simulator.__init__(shoe_size=9)
    return jsonify({
        'message' : 'Shoe and count reset successfully'
    })

@app.route('/start', methods=['POST'])
def start():
    user_hand, dealer_hand = simulator.startHand()
    simulator.user_balance -= simulator.minimum_bet
    return jsonify({
        'user_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in user_hand],
        'dealer_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in dealer_hand[:1]],  # Only show one dealer card
        'message': 'Hands dealt'
    })

@app.route('/hit', methods=['POST'])
def hit():
    card = simulator.userHit()
    hand_value = simulator.calculateHandValue(simulator.getUserHand())
    if hand_value > 21:
        simulator.double_bet = False
    return jsonify({
        'card': playingCard(rank=card[0], suit=card[1]).prettyReturn(),
        'hand_value': hand_value,
        'message': 'User hit'
    })

@app.route('/stand', methods=['POST'])
def stand():
    # Dealer hits until their hand value is 17 or higher
    while simulator.calculateHandValue(simulator.getDealerHand()) < 17:
        simulator.dealerHit()

    user_value = simulator.calculateHandValue(simulator.getUserHand())
    dealer_value = simulator.calculateHandValue(simulator.getDealerHand())

    # if user_value > 21:
    #     result = 'User busts! Dealer wins.'
    #     outcome = 'loss'
    if dealer_value > 21:
        result = 'Dealer busts! User wins.'
        outcome = 'win'
    elif user_value > dealer_value:
        result = 'User wins!'
        outcome = 'win'
    elif user_value < dealer_value:
        result = 'Dealer wins!'
        outcome = 'loss'
    else:
        result = 'It\'s a tie!'
        outcome = 'tie'
    print(simulator.double_bet)
    simulator.resolve_bets(outcome)


    return jsonify({
        'user_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in simulator.getUserHand()],
        'dealer_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in simulator.getDealerHand()],
        'user_value': user_value,
        'dealer_value': dealer_value,
        'result': result,
        'balance':simulator.get_balance()
    })

@app.route('/increasebet', methods=['POST'])
def increase_bet():
    simulator.minimum_bet += 5
    return jsonify({'min_bet': simulator.get_minbet()})

@app.route('/decreasebet', methods=['POST'])
def decrease_bet():
    if simulator.minimum_bet > 5:
        simulator.minimum_bet -= 5  
    return jsonify({'min_bet': simulator.get_minbet()})

@app.route('/doublebet', methods=['POST'])
def double_down():
    simulator.double_bet = True
    simulator.user_balance -= simulator.get_minbet()
    return jsonify({'double_down': 'True'})


@app.route('/balance', methods=['GET'])
def get_balance():
    return jsonify({'balance': simulator.get_balance()})

@app.route('/minbet', methods=['GET'])
def get_minbet():
    if simulator.double_bet:
        min_bet = simulator.get_minbet()*2
    else:
        min_bet = simulator.get_minbet()
    return jsonify({'min_bet': min_bet})

@app.route('/get_count', methods=['GET'])
def get_count():
    return jsonify({"card_count": simulator.getCurrentCount()})

@app.route('/get_true_count', methods=['GET'])
def get_true_count():
    return jsonify({"card_true_count": simulator.getTrueCount()})

@app.route('/get_decks_remain', methods=['GET'])
def get_decks_remain():
    return jsonify({"decks_remain": round(simulator.getStartingShoeSize()/52*(simulator.getShoeSize()/simulator.getStartingShoeSize()))})

@app.route('/get_policy', methods=['GET'])
def get_policy():
    return jsonify({"policy": simulator.getPolicy()})

if __name__ == "__main__":
    simulator = blackJackSim(shoe_size=9)
    app.run(debug=True)
