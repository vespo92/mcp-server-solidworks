# Base adapter class
class SolidWorksAdapter:
    def __init__(self):
        self.connected = False
    
    async def connect(self):
        self.connected = True
    
    async def disconnect(self):
        self.connected = False
