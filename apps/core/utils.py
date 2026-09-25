def client_ip(request):
    # Heroku router дописує реальний IP клієнта в кінець X-Forwarded-For.
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR")
