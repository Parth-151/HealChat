from django.shortcuts import render, redirect

def signin(request):
    if request.method == 'POST':
        return redirect('chatbot:chat')
    return render(request, 'signin.html')