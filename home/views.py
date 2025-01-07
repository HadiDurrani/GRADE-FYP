from django.shortcuts import render
from django.http import JsonResponse
from question_generator.generate_questions import generate_questions_based_on_clos
# Create your views here.
def home(request):
    return render(request, 'home/index.html')

def learnmore(request):
    return render(request, 'home/learnmore.html')

def login(request):
    return render(request, 'home/login.html')

def sandbox(request):
    if request.method == "POST":
        data = request.POST
        num_questions = int(data.get("num_questions", 0))
        questions = []
        for i in range(num_questions):
            clo = data.get(f"clo_{i}")
            qtype = data.get(f"type_{i}")
            generated = generate_questions_based_on_clos({clo: 1}, qtype)  # Generate one question at a time
            questions.extend(generated)

        return JsonResponse({"questions": questions})

    return render(request, "home/sandbox.html")
