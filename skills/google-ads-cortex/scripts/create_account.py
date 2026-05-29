#!/usr/bin/env python3
"""Create a new Google Ads customer account under MCC."""

import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def load_client():
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "login_customer_id": os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"],
        "use_proto_plus": True,
    }
    token = config["developer_token"][:6] + "..." + config["developer_token"][-4:]
    print(f"Client inicializado via /Users/samuelleite/.claude/skills/google-ads-cortex/.env (token: {token})", file=sys.stderr)
    return GoogleAdsClient.load_from_dict(config)


def create_account(client, account_name, currency="BRL", timezone="America/Sao_Paulo"):
    customer_service = client.get_service("CustomerService")

    customer = client.get_type("Customer")
    customer.descriptive_name = account_name
    customer.currency_code = currency
    customer.time_zone = timezone

    try:
        response = customer_service.create_customer_client(
            customer_id=os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"],
            customer_client=customer,
        )
        new_id = response.resource_name.split("/")[1]
        result = {
            "resource_name": response.resource_name,
            "customer_id": new_id,
            "account_name": account_name,
            "currency": currency,
            "timezone": timezone,
            "invite_link": response.invitation_link if hasattr(response, "invitation_link") else None,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return new_id
    except GoogleAdsException as ex:
        error_info = {
            "error": True,
            "message": str(ex),
            "errors": [
                {"error_code": str(e.error_code), "message": e.message}
                for e in ex.failure.errors
            ],
        }
        print(json.dumps(error_info, indent=2, ensure_ascii=False))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create new Google Ads account under MCC")
    parser.add_argument("--name", required=True, help="Account descriptive name")
    parser.add_argument("--currency", default="BRL", help="Currency code (default: BRL)")
    parser.add_argument("--timezone", default="America/Sao_Paulo", help="Timezone (default: America/Sao_Paulo)")
    args = parser.parse_args()

    client = load_client()
    create_account(client, args.name, args.currency, args.timezone)


if __name__ == "__main__":
    main()
