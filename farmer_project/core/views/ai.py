def ai_chat(request):
    TEXT = load_language(request)
    lang = request.session.get("lang")

    prompt_prefix = {
        "te": "తెలుగులో రైతులకు సులభంగా సమాధానం ఇవ్వు.",
        "hi": "किसानों के लिए सरल हिंदी में उत्तर दें।",
        "ta": "விவசாயிகளுக்கு எளிய தமிழில் பதிலளிக்கவும்.",
    }

    final_prompt = prompt_prefix.get(lang, "") + request.POST.get("question")
