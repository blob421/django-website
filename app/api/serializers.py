from rest_framework import serializers

from dashboard.models import UserProfile, Team, Messages, Task, Document

class UserprofileSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()
    role = serializers.StringRelatedField()
    class Meta:
        model = UserProfile
        fields =    '__all__'

    def get_picture(self, obj):
        document = Document.objects.filter(object_id=obj.id).last()
        return document.file.name if document else None
    
class TeamMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['pinned_msg']

class TeamSerializer(serializers.Serializer):
    active_task = serializers.CharField(source='active_task.name')
    class Meta:
        model = UserProfile
        fields = '__all__'

class MessagesSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Messages
        fields = '__all__'
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