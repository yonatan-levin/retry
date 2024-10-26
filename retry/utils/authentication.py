from aiohttp import BasicAuth

class Authentication:
    def __init__(self, auth_type=None, credentials=None):
        """
        Initialize the Authentication module.

        :param auth_type: Type of authentication ('basic', 'token', or None).
        :param credentials: A dictionary containing authentication credentials.
        """
        self.auth_type = auth_type
        self.credentials = credentials or {}

    def get_auth(self):
        """
        Returns the appropriate authentication headers or object.

        :return: Authentication headers or aiohttp BasicAuth object.
        """
        if self.auth_type == 'basic':
            username = self.credentials.get('username')
            password = self.credentials.get('password')
            return BasicAuth(login=username, password=password)
        elif self.auth_type == 'token':
            token = self.credentials.get('token')
            return {'Authorization': f'Bearer {token}'}
        else:
            return None
