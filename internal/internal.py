import requests
import base64
import aiohttp
import asyncio


class ApiCredentials:
    def __init__(self, username, password):
        """
        Initializes an instance of ApiCredentials.

        Args:
            username (str): The username for API authentication.
            password (str): The password for API authentication.
        """
        self.username = username
        self.password = password

    def get_encoded_credentials(self):
        """
        Returns the Base64 encoded username and password for API authentication.
        """
        credentials = f"{self.username}:{self.password}"
        return base64.b64encode(credentials.encode()).decode()


class Client:
    def __init__(self, base_url, api_credentials):
        self.base_url = base_url
        self.api_credentials = api_credentials
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.api_credentials.get_encoded_credentials()}",
        }

    def req(self, payload, method, config):
        try:
            if method == "POST":
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=config["timeout"],
                )
            elif method == "GET":
                response = requests.get(
                    self.base_url, headers=self.headers, timeout=config["timeout"]
                )
            else:
                print(f"Unsupported method: {method}")
                return None

            response.raise_for_status()

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error occurred: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(
                f"Timeout error. The request to {self.base_url} with method {method} has timed out."
            )
            return None
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            print(response.text)
            return None
        except requests.exceptions.RequestException as err:
            print(f"Error occurred: {err}")
            return None


class ClientAsync:

    def __init__(self, base_url, api_credentials):
        self.base_url = base_url
        self.api_credentials = api_credentials
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.api_credentials.get_encoded_credentials()}",
        }

    async def get_job_id(self, payload, user_session):
        try:
            async with user_session.post(
                self.base_url, headers=self.headers, json=payload
            ) as response:
                data = await response.json()
                response.raise_for_status()
                return data["id"]
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error occurred: {e.status} - {e.message} - {data['message']}")
        except aiohttp.ClientConnectionError as e:
            print(f"Connection error occurred: {e}")
        except asyncio.TimeoutError:
            print(f"Timeout error. The request to {self.base_url} has timed out.")
        except Exception as e:
            print(f"An error occurred: {e} - {data['message']}")
        return None

    async def poll_job_status(self, job_id, poll_interval, user_session):
        job_status_url = f"{self.base_url}/{job_id}"
        while True:
            try:
                async with user_session.get(
                    job_status_url, headers=self.headers
                ) as response:
                    data = await response.json()
                    response.raise_for_status()
                    if data["status"] == "done":
                        return True
                    elif data["status"] == "faulted":
                        raise Exception("Job faulted")
            except aiohttp.ClientResponseError as e:
                print(f"HTTP error occurred: {e.status} - {e.message} - {data['message']}")
                return None
            except aiohttp.ClientConnectionError as e:
                print(f"Connection error occurred: {e}")
                return None
            except asyncio.TimeoutError:
                print(f"Timeout error. The request to {job_status_url} has timed out.")
                return None
            except Exception as e:
                print(f"Unexpected error processing your query: {e}")
                return None
            await asyncio.sleep(poll_interval)

    async def get_http_resp(self, job_id, user_session):
        result_url = f"{self.base_url}/{job_id}/results"
        try:
            async with user_session.get(result_url, headers=self.headers) as response:
                data = await response.json()
                response.raise_for_status()
                return response
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error occurred: {e.status} - {e.message} - {data['message']}")
        except aiohttp.ClientConnectionError as e:
            print(f"Connection error occurred: {e}")
        except asyncio.TimeoutError:
            print(f"Timeout error. The request to {result_url} has timed out.")
        except Exception as e:
            print(f"An error occurred: {e} - {data['message']}")
        return None

    async def execute_with_timeout(self, payload, config, user_session):

        job_id = await self.get_job_id(payload, user_session)

        await self.poll_job_status(job_id, config["poll_interval"], user_session)

        result = await self.get_http_resp(job_id, user_session)
        return result
