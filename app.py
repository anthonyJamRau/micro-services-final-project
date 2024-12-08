import random
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from helper_card import playingCard
import itertools
from dotenv import load_dotenv
import os
from policy_definition import return_policy
from flask_sqlalchemy import SQLAlchemy
from flask import session
import uuid
import json
from sqlalchemy import func

load_dotenv()
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:example@mysql/blackjack'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)



class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    login_time = db.Column(db.DateTime, default=db.func.current_timestamp())

class UsageLogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    status_code = db.Column(db.Integer,nullable=False)

class UsageStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    game_id = db.Column(db.String(255), nullable=True)
    hand_id = db.Column(db.String(255), nullable = True)
    action_type = db.Column(db.String(255),nullable = True)
    game_state = db.Column(db.JSON,nullable = True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

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
        if len(hand) == 0:
            return 0
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
                self.user_balance += self.minimum_bet*4
            else:
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


@app.after_request
def log_usage(response):
    user_id = session.get('user_id',None)

    endpoint = request.endpoint or request.path
    method = request.method
    status_code = response.status_code

    try:
        usageLog = UsageLogs(user_id=user_id,endpoint=endpoint,method=method,status_code=status_code)
        db.session.add(usageLog)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to log request: {e}")

    return response

def log_game_action(session_id,user_id,game_id,hand_id,action,game_state):
    try:
        game_log = UsageStats(
            session_id=session_id,
            user_id=user_id,
            game_id=game_id,
            hand_id=hand_id,
            action_type=action,
            game_state=json.dumps(game_state)
        )
        db.session.add(game_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to log game action: {e}")
    return
    
@app.route("/")
def index():
    google_data = None
    user_info_endpoint = '/oauth2/v2/userinfo'
    
    if google.authorized:
        try:
            google_data = google.get(user_info_endpoint).json()
        except:
            return redirect(url_for("google.login"))
        
    if google_data:
        email = google_data.get("email")
        name = google_data.get("name")
        user = Users.query.filter_by(email=email).first()
        if not user:
            user = Users(email=email, name=name)
            db.session.add(user)
            db.session.commit()

        session['user_id'] = user.id
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

    return render_template('index_v3.j2', google_data=google_data)

@app.route('/login')
def login():
    return redirect(url_for('google.login'))


@app.route('/reset',methods = ['POST'])
def reset():
    session['game_id'] = str(uuid.uuid4())

    simulator.__init__(shoe_size=9)
    return jsonify({
        'message' : 'Shoe and count reset successfully'
    })

@app.route('/start', methods=['POST'])
def start():
    if 'game_id' not in session:
        session['game_id'] = str(uuid.uuid4())
    
    session['hand_id'] = str(uuid.uuid4())
    session_id = session['session_id']
    game_id = session['game_id']
    hand_id = session['hand_id']
    user_id = session['user_id']

    user_hand, dealer_hand = simulator.startHand()
    simulator.user_balance -= simulator.minimum_bet

    log = log_game_action(session_id,user_id,game_id,hand_id,'hand-start',{
        'user_hand':simulator.calculateHandValue(simulator.getUserHand()),
        'dealer_hand':simulator.calculateHandValue(simulator.getDealerHand()),
        'balance':simulator.get_balance(),
        'count':simulator.getCurrentCount(),
        'true_count':simulator.getTrueCount(),
        'bet': simulator.get_minbet()*2 if simulator.double_bet else simulator.get_minbet()
    })
    return jsonify({
        'user_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in user_hand],
        'dealer_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in dealer_hand[:1]],  # Only show one dealer card
        'message': 'Hands dealt'
    })

@app.route('/hit', methods=['POST'])
def hit():

    card = simulator.userHit()
    hand_value = simulator.calculateHandValue(simulator.getUserHand())

    session_id = session['session_id']
    game_id = session['game_id']
    hand_id = session['hand_id']
    user_id = session['user_id']

    log = log_game_action(session_id,user_id,game_id,hand_id,'post-hit',{
        'user_hand':hand_value,
        'dealer_hand':simulator.calculateHandValue(simulator.getDealerHand()),
        'balance':simulator.get_balance(),
        'count':simulator.getCurrentCount(),
        'true_count':simulator.getTrueCount(),
        'bet': simulator.get_minbet()*2 if simulator.double_bet else simulator.get_minbet()
    })

    if hand_value > 21:
        simulator.double_bet = False
    return jsonify({
        'card': playingCard(rank=card[0], suit=card[1]).prettyReturn(),
        'hand_value': hand_value,
        'message': 'User hit'
    })

@app.route('/stand', methods=['POST'])
def stand():


    while simulator.calculateHandValue(simulator.getDealerHand()) < 17:
        simulator.dealerHit()

    user_value = simulator.calculateHandValue(simulator.getUserHand())
    dealer_value = simulator.calculateHandValue(simulator.getDealerHand())


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


    session_id = session['session_id']
    game_id = session['game_id']
    hand_id = session['hand_id']
    user_id = session['user_id']

    log = log_game_action(session_id,user_id,game_id,hand_id,'post-stand',{
        'user_hand':user_value,
        'dealer_hand':dealer_value,
        'balance':simulator.get_balance(),
        'count':simulator.getCurrentCount(), 
        'true_count':simulator.getTrueCount(),
        'bet': simulator.get_minbet()*2 if simulator.double_bet else simulator.get_minbet()
    })

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

@app.route('/admin/usage', methods=['GET'])
def admin_usage():
    try:
        total_requests = db.session.query(func.count(UsageLogs.id)).scalar()
        successes = db.session.query(func.count(UsageLogs.id)).filter(
            UsageLogs.status_code.between(200, 299)
        ).scalar()
        failures = db.session.query(func.count(UsageLogs.id)).filter(
            UsageLogs.status_code >= 400
        ).scalar()
        authorizations = db.session.query(func.count(UsageLogs.id)).filter(
            UsageLogs.status_code == 300
        ).scalar()

        endpoint_stats = db.session.query(
            UsageLogs.endpoint,
            func.count(UsageLogs.id).label('request_count')
        ).group_by(UsageLogs.endpoint).all()

        endpoint_data = [
            {
                "endpoint": stat.endpoint,
                "request_count": stat.request_count
            }
            for stat in endpoint_stats
        ]
        return render_template(
            'admin_usage.html',
            total_requests=total_requests,
            successes=successes,
            failures=failures,
            authorizations=authorizations,
            endpoint_data=endpoint_data
        )

    except Exception as e:
        return render_template('error.html', message=str(e)), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    simulator = blackJackSim(shoe_size=9)
    app.run(debug=True, host = '0.0.0.0', port=5000)
