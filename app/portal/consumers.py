import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
     
        user = self.scope["user"]
        print(f"Resolved user: {user} | Authenticated: {user.is_authenticated}")

        if user.is_authenticated:
            self.group_name = f"user_{user.id}"
            await self.channel_layer.group_add(f"user_{user.id}", self.channel_name)
            print(f"User {user.id} connected to group {self.group_name}")
        else:
            print('user_not_auth')
        await self.accept()
        await self.send(text_data=json.dumps({'message': 'WebSocket connected'}))

    async def disconnect(self, close_code):
       user = self.scope["user"]
       if user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        print("Fallback receive triggered:", text_data)
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({'echo': data}))

    async def message(self, event):
       print("message_saved triggered")
       print(event['message'])
       await self.send(text_data=json.dumps({
      
        'message': event['message'],
        'type':event['type']
    }))

