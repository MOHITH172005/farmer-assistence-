def set_language(request):
    if request.method == "POST":
        request.session["lang"] = request.POST.get("language")
    return redirect("login")
