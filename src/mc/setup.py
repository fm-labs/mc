import secrets
import logging

from mc.users import USERS_FILE, create_user_file, add_user, get_user

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAME = "operator"

def setup_admin_auth():
    """
    Check if an admin credentials exists. If not, create one with random password and print it to the console.
    """
    try:
        logger.info("Initializing admin auth ...")
        create_user_file(USERS_FILE)
        try:
            admin_user = get_user(DEFAULT_ADMIN_USERNAME)
        except KeyError as e:
            logger.warning("Admin user not found, creating one with random password")
            password = secrets.token_urlsafe(16)
            add_user(DEFAULT_ADMIN_USERNAME, password, USERS_FILE)
            logger.info(f"Admin user {DEFAULT_ADMIN_USERNAME} created")
            print("-" * 64)
            print(f"Admin user '{DEFAULT_ADMIN_USERNAME}' created with password: {password}")
            print("Please change this password immediately after logging in for the first time.")
            print("-" * 64)
    except Exception as e:
        logger.error(f"Error setting up admin auth: {e}")
