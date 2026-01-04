def load_language(request):
    lang = request.session.get("lang", "en")

    if lang == "te":
        from core.lang.te import TEXT
    elif lang == "hi":
        from core.lang.hi import TEXT
    elif lang == "ta":
        from core.lang.ta import TEXT
    elif lang == "kn":
        from core.lang.kn import TEXT
    elif lang == "ml":
        from core.lang.ml import TEXT
    else:
        from core.lang.en import TEXT

    return TEXT
