# bot.py - The Interactive Trigger Bot
import os
import requests
import logging
import re

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Constants ---
DOMAIN_FILE = "domains.txt"

# --- Get Secrets from Railway Variables ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# --- Domain Management Functions ---
def load_domains():
    """Loads domains from the DOMAIN_FILE into a set."""
    domains = set()
    if os.path.exists(DOMAIN_FILE):
        with open(DOMAIN_FILE, "r") as f:
            for line in f:
                domain = line.strip().lower()
                if domain:
                    domains.add(domain)
    return domains

def save_domains(domains):
    """Saves domains from a set to the DOMAIN_FILE."""
    with open(DOMAIN_FILE, "w") as f:
        for domain in sorted(list(domains)):
            f.write(domain + "\n")

def is_valid_domain(domain):
    """Basic validation for a domain name."""
    if not isinstance(domain, str) or not domain:
        return False
    # Regex for a basic domain name validation (e.g., example.com, sub.example.co.uk)
    # This regex is not exhaustive but covers common cases.
    if re.match(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$", domain.lower()):
        return True
    return False

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Replies when the /start command is sent."""
    logger.info("Received /start command.")
    await update.message.reply_text("Hello! I am the interactive bot. Send /checknow to get an instant report. Use /add_domain <domain> to add a domain and /delete_domain <domain> to remove one.")


async def checknow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers the reporting script via a webhook."""
    logger.info("Received /checknow command.")

    # 1. Check if the user is authorized
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        logger.warning(
            f"Unauthorized access attempt from chat ID: {update.effective_chat.id}"
        )
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # 2. Trigger the reporting script
    try:
        response = requests.get(WEBHOOK_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        await update.message.reply_text("Report triggered successfully!")
        logger.info("Reporting script triggered successfully.")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error triggering report: {e}")
        logger.error(f"Error triggering reporting script: {e}")

async def add_domain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds a domain to the list."""
    logger.info("Received /add_domain command.")

    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        logger.warning(
            f"Unauthorized access attempt to add domain from chat ID: {update.effective_chat.id}"
        )
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /add_domain <domain_name>")
        return

    domain_to_add = context.args[0].lower()

    if not is_valid_domain(domain_to_add):
        await update.message.reply_text(f"'{domain_to_add}' is not a valid domain format.")
        return

    domains = load_domains()
    if domain_to_add in domains:
        await update.message.reply_text(f"Domain '{domain_to_add}' already exists.")
    else:
        domains.add(domain_to_add)
        save_domains(domains)
        await update.message.reply_text(f"Domain '{domain_to_add}' added successfully.")
    logger.info(f"Domain '{domain_to_add}' added by {update.effective_chat.id}")

async def delete_domain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletes a domain from the list."""
    logger.info("Received /delete_domain command.")

    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        logger.warning(
            f"Unauthorized access attempt to delete domain from chat ID: {update.effective_chat.id}"
        )
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /delete_domain <domain_name>")
        return

    domain_to_delete = context.args[0].lower()

    domains = load_domains()
    if domain_to_delete not in domains:
        await update.message.reply_text(f"Domain '{domain_to_delete}' not found in the list.")
    else:
        domains.remove(domain_to_delete)
        save_domains(domains)
        await update.message.reply_text(f"Domain '{domain_to_delete}' deleted successfully.")
    logger.info(f"Domain '{domain_to_delete}' deleted by {update.effective_chat.id}")

# --- Main ---
def main():
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("checknow", checknow_command))
    application.add_handler(CommandHandler("add_domain", add_domain_command))
    application.add_handler(CommandHandler("delete_domain", delete_domain_command))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
