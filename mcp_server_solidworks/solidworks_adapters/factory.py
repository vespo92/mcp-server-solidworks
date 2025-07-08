# Placeholder adapter factory
class AdapterFactory:
    def get_adapter(self, version):
        return MockAdapter()

class MockAdapter:
    def __init__(self):
        self.connected = False
    
    async def connect(self):
        self.connected = True
    
    async def disconnect(self):
        self.connected = False
    
    async def get_model_info(self):
        return {}
    
    async def get_features(self):
        return []
    
    async def get_configurations(self):
        return []
    
    async def get_mass_properties(self):
        return {}
    
    async def list_open_documents(self):
        return []
    
    async def get_document_info(self, path):
        return {}
