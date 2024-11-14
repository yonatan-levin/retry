from aiohttp import ClientSession, TCPConnector

class SessionManager:
    def __init__(self, headers=None, cookies=None, auth=None, connector=None, proxy=None):        
        """
        Initialize the SessionManager.
        :param headers: Default headers for the session.
        :param cookies: Default cookies for the session.
        :param auth: Authentication object or headers.
        :param connector: A custom aiohttp connector (e.g., for SSL).
        :param proxy: A custom proxy to use for the session.
        """
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.auth = auth
        self.connector = connector
        self.proxy = proxy
        self.session = None  # Initialize session to None
 
    async def __aenter__(self):
        if self.connector is None:
            self.connector = TCPConnector(ssl=False)
        self.session = ClientSession(
            headers=self.headers,
            cookies=self.cookies,
            auth=self.auth,
            connector=self.connector,
            trust_env=True
        )
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def open(self):
        if not self.session:
            if self.connector is None:
                self.connector = TCPConnector(ssl=False)
            self.session = ClientSession(
                headers=self.headers,
                cookies=self.cookies,
                auth=self.auth,
                connector=self.connector,
                trust_env=True
            )
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
            
    
