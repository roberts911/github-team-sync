"""
The configuration file would look like this (sans those // comments):

{
    "authority": "https://login.microsoftonline.com/Enter_the_Tenant_Name_Here",
    "client_id": "your_client_id",
    "scope": ["https://graph.microsoft.com/.default"],
        // Specific to Client Credentials Grant i.e. acquire_token_for_client(),
        // you don't specify, in the code, the individual scopes you want to access.
        // Instead, you statically declared them when registering your application.
        // Therefore the only possible scope is "resource/.default"
        // (here "https://graph.microsoft.com/.default")
        // which means "the static permissions defined in the application".

    "secret": "The secret generated by AAD during your confidential app registration",
        // For information about generating client secret, refer:
        // https://github.com/AzureAD/microsoft-authentication-library-for-python/wiki/Client-Credentials#registering-client-secrets-using-the-application-registration-portal

    "endpoint": "https://graph.microsoft.com/v1.0/users"
        // For this resource to work, you need to visit Application Permissions
        // page in portal, declare scope User.Read.All, which needs admin consent
        // https://github.com/Azure-Samples/ms-identity-python-daemon/blob/master/1-Call-MsGraph-WithSecret/README.md
}

You can then run this sample with a JSON configuration file:

    python sample.py parameters.json
"""

import os
import json
import logging

import requests
import msal

# Optional logging
# logging.basicConfig(level=logging.DEBUG)  # Enable DEBUG log for entire script
# logging.getLogger("msal").setLevel(logging.INFO)  # Optionally disable MSAL DEBUG logs

LOG = logging.getLogger(__name__)


class AzureAD:
    def __init__(self):
        self.AZURE_TENANT_ID = os.environ["AZURE_TENANT_ID"]
        self.AZURE_CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
        self.AZURE_CLIENT_SECRET = os.environ["AZURE_CLIENT_SECRET"]
        self.AZURE_APP_SCOPE = [
            f"https://graph.microsoft.com/.{x}"
            for x in os.environ["AZURE_APP_SCOPE"].split(" ")
        ]
        self.AZURE_API_ENDPOINT = os.environ["AZURE_API_ENDPOINT"]
        self.USERNAME_ATTRIBUTE = os.environ["USERNAME_ATTRIBUTE"]

    def get_access_token(self):
        """
        Get the access token for this Azure Service Principal
        :return access_token:
        """
        app = msal.ConfidentialClientApplication(
            self.AZURE_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}",
            client_credential=self.AZURE_CLIENT_SECRET,
        )

        # Lookup the token in cache
        result = app.acquire_token_silent(self.AZURE_APP_SCOPE, account=None)

        if not result:
            logging.info(
                "No suitable token exists in cache. Let's get a new one from AAD."
            )
            result = app.acquire_token_for_client(scopes=self.AZURE_APP_SCOPE)

        if "access_token" in result:
            print("Successfully authenticated!")
            return result["access_token"]

        else:
            print(result.get("error"))
            print(result.get("error_description"))
            print(
                result.get("correlation_id")
            )  # You may need this when reporting a bug

    def get_group_members(self, token=None, group=None):
        """
        Get a list of members for a given group
        :param token:
        :param group:
        :return:
        """
        member_list = []
        # Calling graph using the access token
        graph_data = requests.get(  # Use token to call downstream service
            f"{self.AZURE_API_ENDPOINT}/groups?$filter=startswith(displayName,'{group}')",
            headers={"Authorization": f"Bearer {token}"}
        ).json()
        # print("Graph API call result: %s" % json.dumps(graph_data, indent=2))
        group_info = json.loads(json.dumps(graph_data, indent=2))["value"][0]
        members = requests.get(
            f'{self.AZURE_API_ENDPOINT}/groups/{group_info["id"]}/members',
            headers={"Authorization": f"Bearer {token}"},
        ).json()["value"]
        for member in members:
            member_list.append(member[self.USERNAME_ATTRIBUTE])
        return member_list


# if __name__ == "__main__":
#     aad = AzureAD()
#     token = aad.get_access_token()
#     members = aad.get_group_members(token=token, group="GitHub-Demo")
#     print(members)
