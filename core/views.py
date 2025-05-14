from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "Xyronix Labs Main Server is live ✅"})