from core.utils.language import load_language

def dashboard(request):
    TEXT = load_language(request)
    return render(request, "dashboard.html", {
        "TEXT": TEXT
    })
