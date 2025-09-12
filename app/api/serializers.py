from rest_framework import serializers
from datetime import datetime
from dashboard.models import UserProfile, Team, Messages, Task, Document
from django.contrib.contenttypes.models import ContentType




class UserprofileSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()
    role = serializers.StringRelatedField()
    class Meta:
        model = UserProfile
        fields =    '__all__'

    def get_picture(self, obj):
        up_content_type = ContentType.objects.get_for_model(UserProfile).id

        document = Document.objects.filter(object_id=obj.id, 
                                           content_type_id=up_content_type).last()
        return document.file.name if document else None
    
class TeamMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['pinned_msg']


class TeamSerializer(serializers.ModelSerializer):
    active_task = serializers.CharField(source='active_task.name',read_only=True, allow_null=True)
    username = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    def get_username(self, obj):
        user = UserProfile.objects.get(id = obj.id)
        return user.user.username
    
    def get_picture(self, obj):
        up_content_type = ContentType.objects.get_for_model(UserProfile).id
        document = Document.objects.filter(object_id=obj.id, 
                                           content_type_id=up_content_type).last()
        return document.file.name if document else 'userprofile/0/avatar.png'
    
    def get_last_login(self, obj):
        user = UserProfile.objects.get(id = obj.id)
        last_login = user.user.last_login 
        return last_login.strftime('%Y-%m-%d %H:%M') if last_login else None
    
    
    class Meta:
        model = UserProfile
        fields = '__all__'

class MessagesSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='user.username', read_only=True)
    documents = serializers.SerializerMethodField()
    class Meta:
        model = Messages
        fields = '__all__'

    def get_documents(self, obj):
        docs = Document.objects.filter(object_id = obj.id)
        return [{'path': doc.file.name, 'name':doc.file_name, 'id':doc.id} for doc in docs]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['timestamp'] = serializers.DateTimeField(
            format="%Y-%m-%d %H:%M",read_only=True)

class TaskSerialier(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['due_date'] = serializers.DateTimeField(
            format="%Y-%m-%d %H:%M",read_only=True)