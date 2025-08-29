# import datetime
# from datetime import timezone
import json
import logging
import os
# import sys
from getpass import getpass

# import readchar
import requests
from garth.exc import GarthHTTPError

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    # GarminConnectConnectionError,
    # GarminConnectTooManyRequestsError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
tokenstore = os.getenv("GARMINTOKENS") or ".garmintokens"
# tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
api = None


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        # Using Oauth1 and OAuth2 token files from directory
        print(
            f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...\n"
        )

        # Using Oauth1 and Oauth2 tokens from base64 encoded string
        # print(
        #     f"Trying to login to Garmin Connect using token data from file '{tokenstore_base64}'...\n"
        # )
        # dir_path = os.path.expanduser(tokenstore_base64)
        # with open(dir_path, "r") as token_file:
        #     tokenstore = token_file.read()

        garmin = Garmin()
        garmin.login(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()
            if result1 == "needs_mfa":  # MFA is required
                mfa_code = get_mfa()
                garmin.resume_login(result2, mfa_code)

            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )

            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login (alternative way)
            # token_base64 = garmin.garth.dumps()
            # dir_path = os.path.expanduser(tokenstore_base64)
            # with open(dir_path, "w") as token_file:
            #     token_file.write(token_base64)
            # print(
            #     f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            # )

            # Re-login Garmin API with tokens
            garmin.login(tokenstore)
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error(err)
            return None

    return garmin


def get_mfa():
    """Get MFA."""

    return input("MFA one-time code: ")


def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password


def save_json(output, filename):
    """Format API output for better readability."""

    # Format the output
    if isinstance(output, (int, str, dict, list)):
        formatted_output = json.dumps(output, indent=4)
    else:
        formatted_output = str(output)

    # Save to a file
    with open(filename, "w") as file:
        file.write(formatted_output)

    print(f"Output saved to {filename}")


if __name__ == "__main__":
    api = init_api(email, password)
    if api:
        output = api.get_activities(0, 1000)
        logger.info("Activities fetched successfully")
        save_json(output, "activities.json")
    else:
        logger.error("Garmin API not initialized")