class playingCard:

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.suits_symbols = {
            'hearts': '♥',
            'diamonds': '♦',
            'clubs': '♣',
            'spades': '♠'
        }

    def prettyReturn_cmd(self):

        # Define the card face with ASCII characters
        card_width = 9
        card_height = 5

        rank_display = str(self.rank)[:2].rjust(2)
        suit_display = self.suits_symbols.get(self.suit, '?')

        # ASCII art card
        card = [
            f"+---------+",
            f"|{rank_display}       |",
            f"|    {suit_display}    |",
            f"|       {rank_display}|",
            f"+---------+"
        ]
        return "\n".join(card)
    
    def prettyReturn(self):
        # Get the suit symbol
        suit_display = self.suits_symbols.get(self.suit, '?')

        # HTML representation of the card
        card_html = f"""
        <div class="card">
            <div class="card-top">{self.rank} {suit_display}</div>
            <div class="card-center">{suit_display}</div>
            <div class="card-bottom">{suit_display} {self.rank}</div>
        </div>
        """
        return card_html