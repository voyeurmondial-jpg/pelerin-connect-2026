import os
import uuid
from datetime import datetime
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from flask_cors import CORS # Note: Pour simplifier dans un seul fichier, on utilise une structure minimaliste
import json
from pymongo import MongoClient

# --- CONFIGURATION MINIMALISTE DJANGO-LIKE ---
# Dans un projet réel, cela serait réparti dans settings.py, urls.py et views.py

if not settings.configured:
    settings.configure(
        DEBUG=os.environ.get("DEBUG", "False") == "True",
        SECRET_KEY=os.environ.get("SECRET_KEY", "secret-pelerin-2026"),
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["*"],
    )

# --- CONNEXION MONGODB ATLAS ---
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['pelerin_db']
collection = db['pelerins']

# --- VUES (LOGIQUE MÉTIER) ---

@csrf_exempt
def list_or_create_pelerins(request):
    if request.method == 'GET':
        try:
            pelerins = list(collection.find().sort("timestamp", -1))
            for p in pelerins:
                p['_id'] = str(p['_id'])
            return JsonResponse(pelerins, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            data['officialId'] = f"PEL-{uuid.uuid4().hex[:6].upper()}"
            data['timestamp'] = datetime.utcnow().timestamp() * 1000
            data['present'] = False
            
            result = collection.insert_one(data)
            data['_id'] = str(result.inserted_id)
            return JsonResponse(data, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def update_presence(request, official_id):
    if request.method == 'PATCH':
        try:
            result = collection.update_one(
                {"officialId": official_id},
                {"$set": {"present": True}}
            )
            if result.matched_count == 0:
                return JsonResponse({"error": "Pèlerin non trouvé"}, status=404)
            return JsonResponse({"message": "Présence confirmée"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

# --- URLS ---
urlpatterns = [
    path('api/pelerins', list_or_create_pelerins),
    path('api/pelerins/<str:official_id>/presence', update_presence),
]

# --- APPLICATION WSGI ---
application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    import sys
    # Pour lancer en local: python app.py runserver
    execute_from_command_line(sys.argv)
