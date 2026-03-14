from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, JSONParser
from rest_framework.response import Response

# Create your views here.

class Process(APIView):
    parser_classes = [FileUploadParser]

    def put (self, request, filename, format = None):
        file_obj = request.data['file']

        return Response(status = 204)
    

class SaveData(APIView):
    parser_classes = [FileUploadParser]

    def put (self, request, filename, format = None):
        file_obj = request.data['file']

        return Response(status = 204)