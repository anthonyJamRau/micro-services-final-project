![Screenshot](https://media.istockphoto.com/id/903362472/photo/gambling-hand-holding-poker-cards-and-money-coins-chips.jpg?s=2048x2048&w=is&k=20&c=WSlfu4Ac1MD5Lhc9yZaxdhBk1ZDzpQLyJOqXWKdw7ec=)

# Project Description
Relatively simple microservices app to help users learn how to and practice counting cards during games of BlackJack \
Beta V1 deployed at [professorblackjack](https://professorblackjack.com) 
## Contributing
1. clone repo
2. create venv and install requirements - I used vscode ide
3. Build images and orchestrate containers docker-compose up -- build (requires docker desktop)
4. If testing with Kubernetes, enable it in Docker and apply the yaml files
5. create PR
## Backlog
### functionality
1. show win probabilites
2. add support for splitting hands
3. change doubling logic since casinos dont allow double bets on Blackjacks
4. update oauth flow to check admin rights
### implementation
1. Not a front end developer. I am a math and algorithms guy, so any front end help would be great!
2. Any ops improvements for logging, env management, database usage - this was a huge learning experience for me.
3. Envisioning a progress bar that shows how ready you are to try counting cards at a Casino.
4. Improve security
```
Folder tree:
├── .venv
├── dockerconfig (for local development and to push images to an online image store like DockerHub)
│   ├── docker-compose.yml
│   ├── Dockerfile.app
│   ├── Dockerfile.db
│   └── init.sql
├── kubeconfig (for deployment on GKE, can build locally with Docker or Minikube) 
│   ├── app-deployment.yaml (local necessary - be sure to expose app service as it will not be linked to Ingress)
│   ├── ingress.yaml (deploymet)
│   ├── managed-cert.yaml (deployment)
│   └── mysql-deployment.yaml (local necessary - pvc store)
├── templates (front ends)
│   ├── admin_usage.html
│   ├── index.j2
│   ├── index_v2.j2
│   └── index_v3.j2 (latest)
├── policy_definition.py
├── helper_card.py
├── requirements.txt
├── app.py (Flask - development)
├── .env

.env example (used for database config and Oauth flow)
GOOGLE_CLIENT_ID= GCP credentials
GOOGLE_CLIENT_SECRET= GCP credentials
secret_key= manually generated


```


# API Documentation for Blackjack Application

This document provides an overview of the main API endpoints for the Blackjack game application. All endpoints respond with JSON data.

## Authentication
The app uses Google OAuth2 for user authentication. Once authenticated, a session is created, and user-specific actions are tied to their session. A database persists in GKE that stores user information and allows for future game analytics to show user improvement etc...

---

## Game Management

### Reset the Game
- **Endpoint**: `/reset`
- **Method**: POST
- **Description**: Resets the game by creating a new shoe and resetting the card count.
- **Response**:
  ```json
  {
    "message": "Shoe and count reset successfully"
  }
  ```
### Start a New Hand
- **Endpoint**: `/reset`
- **Method**: POST
- **Description**: Starts a new hand by dealing cards to the user and dealer. Deducts the minimum bet from the user's balance.
- **Response**:
```json
{
  "user_hand": ["Card 1", "Card 2"],
  "dealer_hand": ["Card 1"],
  "message": "Hands dealt"
}
  ```

### User Hits
- **Endpoint**: `/hit`
- **Method**: POST
- **Description**: Deals one additional card to the user. If the user exceeds 21, they lose the round.

- **Response**:
```json
{
  "card": "Dealt Card",
  "hand_value": 20,
  "message": "User hit"
}
  ```

### User Stands
- **Endpoint**: `/stand`
- **Method**: POST
- **Description**: Finalizes the user’s turn, and the dealer completes their hand. The game determines the winner.

- **Response**:
```json
{
  "user_hand": ["Card 1", "Card 2"],
  "dealer_hand": ["Card 1", "Card 2"],
  "user_value": 20,
  "dealer_value": 18,
  "result": "User wins!",
  "balance": 1050
}
  ```

## Betting
### Increase Bet
- **Endpoint**: `/increasebet`,`/decreasebet`
- **Method**: POST
- **Description**:  Increases/decreases the minimum bet by $5.

- **Response**:
```json
{
  "min_bet": 10
}
  ```
### Double Bet
- **Endpoint**: `/doubleBet`
- **Method**: POST
- **Description**:  Doubles the current bet amount.

- **Response**:
```json
{
  "double_down": "True"
}
  ```
## Game Information
### Get Method Example
### Get Balance
- **Endpoint**: `/balance`,`/minbet`,`/get_count`,`/get_true_count`,`/get_decks_remain`,`/get_policy`
- **Method**: GET
- **Description**:  Retrieves the user's current balance.

- **Response**:
```json
{
  "balance": 950
}
  ```

## Administrative
- **Endpoint**: `/admin/usage`
- **Method**: POST
- **Description**: Provides a summary of API usage, including the total number of requests, successes, and failures.

- **Response**:
```json
{
  "total_requests": 100,
  "successes": 95,
  "failures": 5
}
  ```





