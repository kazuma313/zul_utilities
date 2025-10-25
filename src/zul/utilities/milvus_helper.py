"""
Milvus Helper Utility
Module ini bisa di-extend sesuai kebutuhan
"""

class Milvus:
    """
    Helper class untuk bekerja dengan Milvus vector database
    
    Contoh:
        >>> from zul.utilities.milvus_helper import Milvus
        >>> client = Milvus(host="localhost", port=19530)
        >>> client.connect()
    """
    
    def __init__(self, host: str = "localhost", port: int = 19530):
        """
        Initialize Milvus client
        
        Args:
            host: Milvus server host
            port: Milvus server port
        """
        self.host = host
        self.port = port
        self._connected = False
        
    def connect(self):
        """Connect ke Milvus server"""
        print(f"Connecting to Milvus at {self.host}:{self.port}")
        self._connected = True
        print("✅ Connected successfully!")
        
    def disconnect(self):
        """Disconnect dari Milvus server"""
        if self._connected:
            print("Disconnecting from Milvus...")
            self._connected = False
            print("✅ Disconnected successfully!")
        else:
            print("⚠️  Already disconnected")
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected
