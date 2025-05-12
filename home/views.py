from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from .models import User, Classroom, Enrollment
from .forms import CreateClassForm, JoinClassForm
from Generate_assignment_FLAN.FlanGenLora import generate_questions_based_on_clos

# ------------------- Home and Other Pages -------------------
def home(request):
    return render(request, 'home/index.html')

def learnmore(request):
    return render(request, 'home/learnmore.html')

import os
import PyPDF2
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from sentence_transformers import SentenceTransformer
from transformers import RobertaTokenizer, T5ForConditionalGeneration
from Eval_Assignment.Code import evaluate_code
from Eval_Assignment.Theory import evaluate_theory

# Hardcoded reference solutions (for now)
REFERENCE_THEORY = "A stack is a data structure that stores function calls and local variables, while stack_size refers to the allocated memory limit for the stack."
REFERENCE_CODE = """
def is_numeric(element):
    return isinstance(element, (int, float))
lst = [10, "hello", 3.14, True]
print([is_numeric(i) for i in lst])
"""

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()

# ✅ Load models only once in Django
bert_model = SentenceTransformer("all-MiniLM-L6-v2")
code_tokenizer = RobertaTokenizer.from_pretrained("Salesforce/codet5-base")
code_model = T5ForConditionalGeneration.from_pretrained("Salesforce/codet5-base")

import re

def sandbox(request):
    if request.method == "POST" and request.FILES.get("assignmentFile"):
        uploaded_file = request.FILES["assignmentFile"]
        fs = FileSystemStorage()
        file_path = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(file_path)

        extracted_text = extract_text_from_pdf(file_path)

        # ✅ Debugging print statement
        print("\n=== Extracted Text from PDF ===\n", extracted_text, "\n=============================\n")

        # ✅ Improved Segmentation using Regular Expressions
        answers = re.split(r"\n\s*\n", extracted_text.strip())  # Splits by empty lines

        results = []
        for answer in answers:
            answer = answer.strip()
            if "def " in answer and ":" in answer:  # Detects code
                score = evaluate_code(answer, REFERENCE_CODE, code_tokenizer, code_model)
                category = "Code"
            else:
                score = evaluate_theory(answer, REFERENCE_THEORY, bert_model)
                category = "Theory"

            results.append({"answer": answer, "score": score, "category": category})
        print(results)
        os.remove(file_path)

        return render(request, "home/sandbox.html", {"results": results})

    return render(request, "home/sandbox.html")


# ------------------- Authentication (UNCHANGED) -------------------
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = make_password(request.POST['password'])
        user_type = request.POST['user_type']

        if User.objects.filter(username=username).exists():
            return render(request, 'home/signup.html', {'error': 'Username already taken'})
        elif User.objects.filter(email=email).exists():
            return render(request, 'home/signup.html', {'error': 'Account with same Email exists'})

        user = User(username=username, email=email, password=password, user_type=user_type)
        user.save()

        return redirect('home:login')

    return render(request, 'home/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)

            if check_password(password, user.password):
                request.session['user_id'] = str(user.id)
                request.session['user_type'] = user.user_type  # Store user type in session

                # Redirect based on user type
                if user.user_type == "teacher":
                    return redirect('home:teacher_dashboard')
                else:
                    return redirect('home:student_dashboard')
            else:
                return render(request, 'home/login.html', {'error': 'Incorrect password'})  

        except User.DoesNotExist:
            return render(request, 'home/login.html', {'error': 'Username not found'})  

    return render(request, 'home/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('home:home')

# ------------------- Teacher Dashboard -------------------
def teacher_dashboard(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('home:login')

    user = User.objects.get(id=user_id)

    if user.user_type != "teacher":
        return redirect('home:student_dashboard')

    classes = Classroom.objects.filter(teacher=user)

    if request.method == 'POST':
        form = CreateClassForm(request.POST)
        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.teacher = user
            classroom.save()
            messages.success(request, f"Class '{classroom.name}' created with code {classroom.code}")
            return redirect('home:teacher_dashboard')
    else:
        form = CreateClassForm()

    return render(request, 'home/teacher_dashboard.html', {'teacher_name': user.username, 'classes': classes, 'form': form})

# ------------------- Student Dashboard -------------------
def student_dashboard(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('home:login')

    user = User.objects.get(id=user_id)

    if user.user_type != "student":
        return redirect('home:teacher_dashboard')

    enrolled_classes = Enrollment.objects.filter(student=user)

    if request.method == 'POST':
        form = JoinClassForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            classroom = Classroom.objects.filter(code=code).first()
            if classroom:
                Enrollment.objects.get_or_create(student=user, classroom=classroom)
                messages.success(request, f"Joined class {classroom.name}")
                return redirect('home:student_dashboard')
            else:
                messages.error(request, "Invalid class code")
    else:
        form = JoinClassForm()

    return render(request, 'home/student_dashboard.html', {'student_name': user.username, 'enrolled_classes': enrolled_classes, 'form': form})

# ------------------- Assignment Generation (UNCHANGED) -------------------
def generate_assignment(request):
    if request.method == "POST":
        data = request.POST
        num_questions = int(data.get("num_questions", 0))
        questions = []

        for i in range(num_questions):
            clo = data.get(f"clo_{i}")
            qtype = data.get(f"type_{i}")
            generated = generate_questions_based_on_clos({clo: 1}, qtype)  
            questions.extend(generated)

        return JsonResponse({"questions": questions})

    return render(request, "home/generate_assignment.html")

def manage_classes(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('home:login')

    user = User.objects.get(id=user_id)

    if user.user_type != "teacher":
        return redirect('home:student_dashboard')

    classes = Classroom.objects.filter(teacher=user)
    form = CreateClassForm()  # ✅ Initialize the form to avoid reference errors

    if request.method == 'POST':
        form = CreateClassForm(request.POST)
        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.teacher = user
            classroom.save()  # ✅ This saves the class, no need to re-fetch it

            messages.success(request, f"Class '{classroom.name}' created with code {classroom.code}")
            return redirect('home:manage_classes')  # ✅ Reload the page so the new class appears
        else:
            messages.error(request, "Failed to create class. Please check your input.")

    return render(request, 'home/manage_classes.html', {'teacher_name': user.username, 'classes': classes, 'form': form})


from bson import ObjectId  # ✅ Import ObjectId for MongoDB queries

def class_details(request, class_id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('home:login')
    
    user = User.objects.get(id=user_id)

    if user.user_type != "teacher":
        return redirect('home:student_dashboard')

    try:
        classroom = Classroom.objects.get(id=ObjectId(class_id))  # ✅ Convert class_id to ObjectId
        enrolled_students = Enrollment.objects.filter(classroom=classroom)
    except Classroom.DoesNotExist:
        return redirect('home:manage_classes')

    return render(request, 'home/class_details.html', {'classroom': classroom, 'enrolled_students': enrolled_students})


def student_classes(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('home:login')

    user = User.objects.get(id=user_id)

    if user.user_type != "student":
        return redirect('home:teacher_dashboard')

    enrolled_classes = Enrollment.objects.filter(student=user)

    if request.method == 'POST':
        form = JoinClassForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            classroom = Classroom.objects.filter(code=code).first()
            if classroom:
                Enrollment.objects.get_or_create(student=user, classroom=classroom)
                messages.success(request, f"Joined class {classroom.name}")
                return redirect('home:student_classes')
            else:
                messages.error(request, "Invalid class code")
    else:
        form = JoinClassForm()

    return render(request, 'home/student_classes.html', {'student_name': user.username, 'enrolled_classes': enrolled_classes, 'form': form})

from bson import ObjectId  
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Classroom, Enrollment

def delete_class(request, class_id):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("home:login")

        try:
            classroom = get_object_or_404(Classroom, id=ObjectId(class_id))  # ✅ Convert to ObjectId
        except Classroom.DoesNotExist:
            messages.error(request, "Class not found.")
            return redirect("home:manage_classes")

        # Ensure only the teacher who created the class can delete it
        if str(classroom.teacher.id) != user_id:
            messages.error(request, "You can only delete your own classes.")
            return redirect("home:manage_classes")

        # ✅ Fix: Use `classroom` instead of `class_enrolled`
        Enrollment.objects.filter(classroom=classroom).delete()

        # Delete the class
        classroom.delete()

        messages.success(request, f"Class '{classroom.name}' deleted successfully.")
        return redirect("home:manage_classes")

    return redirect("home:manage_classes")
