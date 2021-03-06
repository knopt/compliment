from app.models import Location, Pin, User, Message, BroadcastMessage
from app.serializers import LocationSerializer, PinSerializer, UserSerializer, MessageSerializer, BroadcastMessageSerializer
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response



class UserListCreate(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class LocationList(generics.ListCreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class PinList(generics.ListCreateAPIView):
    queryset = Pin.objects.all()
    serializer_class = PinSerializer


class NearbyUsersList(APIView):
    def get(self, request, format=None):

        dist = 300.0
        user_id = request.GET['user_id']
        user_loc = Location.objects.filter(user_id=user_id).latest('timestamp')
        print(user_loc)

        users = User.objects.all().exclude(auto_id=user_id)
        locations = [Location.objects.filter(user=user).latest('timestamp') for user in users]

        nearby_users = []

        for user, location in zip(users, locations):
            if (abs(location.latitude - user_loc.latitude) < dist) and (abs(location.longitude - user_loc.longitude) < dist):
                nearby_users.append(user)

        serializer = UserSerializer(nearby_users, many=True)
        return Response(serializer.data)


@csrf_exempt
@api_view(['GET'])
def get_messages(request):
    pk = request.GET['user']
    timestamp = request.GET['timestamp']

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponse(status=404)

    messages = Message.objects.all().filter(receiver_id=user.auto_id, seen=False, send_time__gt=timestamp)
    serializer = MessageSerializer(messages, many=True)
    for m in messages:
        m.update()
        m.save()

    for message in serializer.data:
        user_id = message['sender_id']
        user = User.objects.get(pk=user_id)
        message['name'] = user.name
        message['photo'] = user.photo

    return JsonResponse(serializer.data, safe=False)

@csrf_exempt
@api_view(['GET'])
def get_broadcast_messages(request):
    pk = request.GET['user']
    timestamp = request.GET['timestamp']

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponse(status=404)

    messages = BroadcastMessage.objects.all().filter(receiver_id=user.auto_id, seen=False, send_time__gt=timestamp)
    serializer = BroadcastMessageSerializer(messages, many=True)
    for m in messages:
        m.update()
        m.save()

    for message in serializer.data:
        user_id = message['sender_id']
        user = User.objects.get(pk=user_id)
        message['name'] = user.name
        message['photo'] = user.photo

    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['POST'])
def send_message(request):
    data = JSONParser().parse(request)

    try:
        sender = User.objects.get(pk=data["sender_id"])
        receiver = User.objects.get(pk=data["receiver_id"])
    except User.DoesNotExist:
        return HttpResponse(status=404)

    serializer = MessageSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return HttpResponse(status=201)

    return JsonResponse(serializer.errors, status=400)


@csrf_exempt
@api_view(['POST'])
def send_broadcast_message(request):
    data = JSONParser().parse(request)

    try:
        sender = User.objects.get(pk=data["sender_id"])
    except User.DoesNotExist:
        return HttpResponse(status=404)

    data["receiver_id"] = 1

    serializer = BroadcastMessageSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return HttpResponse(status=201)

    return JsonResponse(serializer.errors, status=400)
