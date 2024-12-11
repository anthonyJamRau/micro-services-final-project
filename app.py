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
# app.config['SQLALCHEMY_ECHO'] = True
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

class BlackJackGameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(255), nullable=False)
    shoe = db.Column(db.JSON, nullable=False)
    user_hand = db.Column(db.JSON, nullable=False)
    dealer_hand = db.Column(db.JSON, nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    true_count = db.Column(db.Float, nullable=False, default=0)
    user_balance = db.Column(db.Integer, nullable=False, default=1000)
    double_bet = db.Column(db.Boolean, nullable=False, default=False)
    minimum_bet = db.Column(db.Integer, nullable=False, default=5)
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

class GameStateService:
    @staticmethod
    def save_game_state(user_id, session_id, game_state):
        """Save the game state to the database, updating if the record exists."""
        # Attempt to find an existing record
        existing_state = BlackJackGameState.query.filter_by(user_id=user_id, session_id=session_id).first()

        if existing_state:
            # Update the existing record
            existing_state.shoe = GameStateService.serialize_shoe(game_state.shoe)
            existing_state.user_hand = game_state.user_hand
            existing_state.dealer_hand = game_state.dealer_hand
            existing_state.count = game_state.count
            existing_state.true_count = game_state.true_count
            existing_state.user_balance = game_state.user_balance
            existing_state.double_bet = game_state.double_bet
            existing_state.minimum_bet = game_state.minimum_bet
        else:
            # Create a new record
            state = BlackJackGameState(
                user_id=user_id,
                session_id=session_id,
                shoe=GameStateService.serialize_shoe(game_state.shoe),
                user_hand=game_state.user_hand,
                dealer_hand=game_state.dealer_hand,
                count=game_state.count,
                true_count=game_state.true_count,
                user_balance=game_state.user_balance,
                double_bet=game_state.double_bet,
                minimum_bet=game_state.minimum_bet
            )
            db.session.add(state)

        db.session.commit()

    @staticmethod
    def load_game_state(user_id, session_id):
        """Load the game state from the database."""
        state = BlackJackGameState.query.filter_by(
            user_id=user_id, session_id=session_id
        ).first()
        if not state:
            return None
        
        shoe = GameStateService.deserialize_shoe(state.shoe)
        # Recreate the blackJackSim instance using the stored state
        # You should use the shoe size or pass it as an argument if needed
        game_state = blackJackSim(shoe_size=6)  # placeholder
        game_state.count = state.count
        game_state.true_count = state.true_count
        game_state.user_balance = state.user_balance
        game_state.shoe = shoe  # This will load the shoe state as a list of tuples
        game_state.user_hand = state.user_hand  # Load user hand
        game_state.dealer_hand = state.dealer_hand  # Load dealer hand
        game_state.minimum_bet = state.minimum_bet
        game_state.double_bet = state.double_bet

        return game_state
    @staticmethod
    def serialize_shoe(shoe):
        """Convert the shoe (list of tuples) into a JSON string."""
        return json.dumps(shoe)

    @staticmethod
    def deserialize_shoe(shoe_str):
        """Convert a JSON string back into the shoe (list of tuples)."""
        return json.loads(shoe_str)
    


def log_usage(request,response):
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
    user_id=session['user_id']
    session_id=session['session_id']

    game_state = blackJackSim(shoe_size=6)

    decks_remain = round(game_state.getStartingShoeSize()/52*(game_state.getShoeSize()/game_state.getStartingShoeSize()))
    card_count = game_state.getCurrentCount()
    true_count = game_state.getTrueCount()
    balance = game_state.get_balance()
    min_bet = game_state.get_minbet()

    response = jsonify({
        'decks_remain':decks_remain,
        'card_count':card_count,
        'true_count':true_count,
        'balance':balance,
        'min_bet':min_bet,
        'message': 'Hands dealt'
    })

    GameStateService.save_game_state(user_id,session_id,game_state)
    log_usage(request,response)
    return response


@app.route('/start', methods=['POST'])
def start():
    if 'game_id' not in session:
        session['game_id'] = str(uuid.uuid4())
    
    session['hand_id'] = str(uuid.uuid4())
    session_id = session['session_id']
    game_id = session['game_id']
    hand_id = session['hand_id']
    user_id = session['user_id']

    game_state = GameStateService.load_game_state(user_id, session_id)
    if not game_state:
        game_state = blackJackSim(shoe_size=6)     
    

    user_hand, dealer_hand = game_state.startHand()
    game_state.user_balance -= game_state.minimum_bet
    decks_remain = round(game_state.getStartingShoeSize()/52*(game_state.getShoeSize()/game_state.getStartingShoeSize()))
    card_count = game_state.getCurrentCount()
    true_count = game_state.getTrueCount()
    balance = game_state.get_balance()

    log = log_game_action(session_id,user_id,game_id,hand_id,'hand-start',{
        'user_hand':game_state.calculateHandValue(game_state.getUserHand()),
        'dealer_hand':game_state.calculateHandValue(game_state.getDealerHand()),
        'balance':game_state.get_balance(),
        'count':game_state.getCurrentCount(),
        'true_count':game_state.getTrueCount(),
        'bet': game_state.get_minbet()*2 if game_state.double_bet else game_state.get_minbet()
    })
    
    response = jsonify({
        'user_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in user_hand],
        'dealer_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in dealer_hand[:1]],
        'decks_remain':decks_remain,
        'card_count':card_count,
        'true_count':true_count,
        'balance':balance,
        'message': 'Hands dealt'
    })
    GameStateService.save_game_state(user_id,session_id,game_state)
    log_usage(request,response)
    return response


@app.route('/hit', methods=['POST'])
def hit():
    

    session_id = session['session_id']
    game_id = session['game_id']
    hand_id = session['hand_id']
    user_id = session['user_id']

    game_state = GameStateService.load_game_state(user_id, session_id)

    card = game_state.userHit()
    hand_value = game_state.calculateHandValue(game_state.getUserHand())
    card_count = game_state.getCurrentCount()

    log = log_game_action(session_id,user_id,game_id,hand_id,'post-hit',{
        'user_hand':hand_value,
        'dealer_hand':game_state.calculateHandValue(game_state.getDealerHand()),
        'balance':game_state.get_balance(),
        'count':game_state.getCurrentCount(),
        'true_count':game_state.getTrueCount(),
        'bet': game_state.get_minbet()*2 if game_state.double_bet else game_state.get_minbet()
    })

    if hand_value > 21:
        game_state.double_bet = False
    
    response = jsonify({
        'card': playingCard(rank=card[0], suit=card[1]).prettyReturn(),
        'hand_value': hand_value,
        'card_count':card_count,
        'message': 'User hit'
    })

    GameStateService.save_game_state(user_id,session_id,game_state)
    log_usage(request,response)
    return response

@app.route('/stand', methods=['POST'])
def stand():
    
    session_id = session['session_id']
    user_id = session['user_id']
    game_id = session['game_id']
    hand_id = session['hand_id']
    

    game_state = GameStateService.load_game_state(user_id, session_id)

    while game_state.calculateHandValue(game_state.getDealerHand()) < 17:
        game_state.dealerHit()

    user_value = game_state.calculateHandValue(game_state.getUserHand())
    dealer_value = game_state.calculateHandValue(game_state.getDealerHand())
    decks_remain = round(game_state.getStartingShoeSize()/52*(game_state.getShoeSize()/game_state.getStartingShoeSize()))


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




    log = log_game_action(session_id,user_id,game_id,hand_id,'post-stand',{
        'user_hand':user_value,
        'dealer_hand':dealer_value,
        'balance':game_state.get_balance(),
        'card_count':game_state.getCurrentCount(), 
        'true_count':game_state.getTrueCount(),
        'min_bet': game_state.get_minbet()*2 if game_state.double_bet else game_state.get_minbet(),
        'decks_remain':decks_remain
    })

    game_state.resolve_bets(outcome)
    
    response = jsonify({
        'user_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in game_state.getUserHand()],
        'dealer_hand': [playingCard(rank=card[0], suit=card[1]).prettyReturn() for card in game_state.getDealerHand()],
        'user_value': user_value,
        'dealer_value': dealer_value,
        'result': result,
        'balance':game_state.get_balance(),
        'card_count':game_state.getCurrentCount(),
        'true_count':game_state.getTrueCount(),
        'decks_remain':decks_remain,
        'min_bet':game_state.get_minbet()
    })

    GameStateService.save_game_state(user_id,session_id,game_state)
    log_usage(request,response)
    return response

@app.route('/increasebet', methods=['POST'])
def increase_bet():
    session_id = session['session_id']
    user_id = session['user_id']
    
    game_state = GameStateService.load_game_state(user_id, session_id)
    if not game_state:
        game_state = blackJackSim(shoe_size=6)  
    game_state.minimum_bet += 5
    
    response = jsonify({'min_bet': game_state.get_minbet()})

    GameStateService.save_game_state(user_id,session_id,game_state)
    log_usage(request,response)
    return response

@app.route('/decreasebet', methods=['POST'])
def decrease_bet():
    session_id = session['session_id']
    user_id = session['user_id']
    
    game_state = GameStateService.load_game_state(user_id, session_id)
    if not game_state:
        game_state = blackJackSim(shoe_size=6)  

    if game_state.minimum_bet > 5:
        game_state.minimum_bet -= 5
    
    response = jsonify({'min_bet': game_state.get_minbet()})

    GameStateService.save_game_state(user_id,session_id,game_state)
    log_usage(request,response)
    return response

@app.route('/doublebet', methods=['POST'])
def double_down():
    session_id = session['session_id']
    user_id = session['user_id']
    
    game_state = GameStateService.load_game_state(user_id, session_id)
    game_state.double_bet = True
    min_bet = game_state.get_minbet()*2
    game_state.user_balance -= game_state.get_minbet()

    response = jsonify({'double_down': 'True',
                        'min_bet':min_bet,
                        'balance':game_state.get_balance()})

    GameStateService.save_game_state(user_id,session_id,game_state)
    log_usage(request,response)
    return response


@app.route('/balance', methods=['GET'])
def get_balance():   

    session_id = session['session_id']
    user_id = session['user_id']
    
    game_state = GameStateService.load_game_state(user_id, session_id)
    response = jsonify({'balance': game_state.get_balance()})
    log_usage(request,response)
    return response

@app.route('/minbet', methods=['GET'])
def get_minbet():
    session_id = session['session_id']
    user_id = session['user_id']
    
    game_state = GameStateService.load_game_state(user_id, session_id)
    if game_state.double_bet:
        min_bet = game_state.get_minbet()*2
    else:
        min_bet = game_state.get_minbet()
    
    response = jsonify({'min_bet': min_bet})

    log_usage(request,response)
    return response

@app.route('/get_count', methods=['GET'])
def get_count():

    session_id = session['session_id']
    user_id = session['user_id']
    
    game_state = GameStateService.load_game_state(user_id, session_id)
    response = jsonify({"card_count": game_state.getCurrentCount()})

    log_usage(request,response)
    return response

@app.route('/get_true_count', methods=['GET'])
def get_true_count():
    session_id = session['session_id']
    user_id = session['user_id']
    game_state = GameStateService.load_game_state(user_id, session_id)
    response = jsonify({"card_true_count": game_state.getTrueCount()})
    log_usage(request,response)
    return response

@app.route('/get_decks_remain', methods=['GET'])
def get_decks_remain():
    session_id = session['session_id']
    user_id = session['user_id']
    
    game_state = GameStateService.load_game_state(user_id, session_id)
    response = jsonify({"decks_remain": round(game_state.getStartingShoeSize()/52*(game_state.getShoeSize()/game_state.getStartingShoeSize()))})
    log_usage(request,response)
    return response

@app.route('/get_policy', methods=['GET'])
def get_policy():
    session_id = session['session_id']
    user_id = session['user_id']
    
    game_state = GameStateService.load_game_state(user_id, session_id)
    response = jsonify({"policy": game_state.getPolicy()})
    log_usage(request,response)
    return response

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
            endpoint_data=endpoint_data
        )

    except Exception as e:
        return render_template('error.html', message=str(e)), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    simulator = blackJackSim(shoe_size=6)

    app.run(debug=True, host = '0.0.0.0', port=5000)
