# Shopee_scrape

Simple program to periodically check changed stock from a shop in shopee.co.id and send notification via telegram.
  
NOTE:
- **PLEASE BE RESPECTFUL TO THE COMPANY AND SHOP.**
- Currently support 1 user only.

## Usage

Change \<telegram bot token> with your telegram bot token.\
Change \<shop> with shopee shop of your choice, example https://shopee.co.id/xxxx pick xxxx.

Install & run

    pip install -r requirement.txt
    python scrape.py

Telegram bot commands:

    /start              # check if your bot is started.
    /set <seconds>      # set the timer, minimum 300s.
    /current            # list of all item.
    /last               # list of latest change.