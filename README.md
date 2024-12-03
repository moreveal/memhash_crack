# RainbowHash Telegram Bot (#MemHash booster)

This project is a Telegram bot designed to facilitate the purchase of a script that boosts mining speed in the game **#MemHash**.

## Features
- User-friendly interface for purchasing the mining speed boost script.
- Automated handling of purchase and refund processes.
- Easily configurable environment variables for deployment flexibility.

---

## Getting Started

### Prerequisites

1. **Python 3.7+**: Ensure you have Python installed. You can download it [here](https://www.python.org/).
2. **Telegram Bot API Token**: Obtain a bot token from [BotFather](https://core.telegram.org/bots#botfather) on Telegram.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/memhash-boost-bot.git
   cd memhash-boost-bot```

2. Set up a virtual environment:
    ```
    python -m venv venv
    source venv/bin/activate # For Windows: venv\Scripts\activate

3. Install dependencies:
    `pip install -r requirements.txt`

4. Set up environment variables:
   
    `RAINBOWHASH_API_TOKEN`: Your bot API token
   
    `RAINBOWHASH_ALL_REFUND`: Whether to enable auto-refund (set to `true` for testing)

    Create a .env file in the project root or export these variables in your environment

    Example `.env` file:
    ```
    RAINBOWHASH_API_TOKEN=your_bot_token
    RAINBOWHASH_ALL_REFUND=true
    ```
6. (Optional) Install the Javascript obfuscator for added security:
```
npm install javascript-obfuscator
```
*Note*: Obfuscation is currently disabled. See the `TODO` section below.

## Running the bot
Start the bot with:
```
python main.py
```

## TODO List:
* Obfuscate Code: Add obfuscation during the build process.
    * Uncomment the JavaScript obfuscator logic in the configuration when this feature is needed

## License
This project is licensed under the MIT License.
