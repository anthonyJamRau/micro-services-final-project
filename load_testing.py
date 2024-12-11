import requests
import threading

BASE_URL = "https://professorblackjack.com"  # Replace with your application URL
SESSION_ID = "0a9248d4-403e-4d2f-b2d3-4abb32794ce2"   # Mock session ID for load testing
USER_ID = "1"

# Simulate playing one game of Blackjack
def play_game():
    try:
        # Start a new hand
        start_response = requests.post(f"{BASE_URL}/start")
        if start_response.status_code != 200:
            print(f"Failed to start hand: {start_response.status_code}")
            return

        # Stand immediately
        stand_response = requests.post(f"{BASE_URL}/stand")
        if stand_response.status_code != 200:
            print(f"Failed to stand: {stand_response.status_code}")
            return

        # Log the result
        result = stand_response.json()
        print(f"Game result: {result['result']}, Balance: {result['balance']}")

    except Exception as e:
        print(f"Error during game simulation: {e}")


# Play 1000 games of Blackjack
def load_test(num_games):
    threads = []
    for i in range(num_games):
        thread = threading.Thread(target=play_game, args=())
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    NUM_GAMES = 1  # Number of games to simulate
    load_test(NUM_GAMES)
