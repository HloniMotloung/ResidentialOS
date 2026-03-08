class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ── Paths that don't need an estate ──────────────────
        SKIP_PATHS = (
            "/admin/",
            "/api/v1/auth/",
            "/static/",
            "/media/",
            "/register/",
            "/logout/",
        )

        if any(request.path.startswith(p) for p in SKIP_PATHS) or request.path == "/":
            return self.get_response(request)

        # ── Resolve estate from session (web) or header (API) ─
        slug = None

        # Web interface stores estate in session
        if request.session.get("estate_slug"):
            slug = request.session["estate_slug"]

        # API calls pass it via header
        elif request.headers.get("X-Estate-Slug"):
            slug = request.headers.get("X-Estate-Slug")

        if slug:
            from apps.estates.models import Estate
            try:
                request.estate = Estate.objects.get(slug=slug, is_active=True)
            except Estate.DoesNotExist:
                from django.http import JsonResponse
                return JsonResponse({"error": "Estate not found."}, status=404)
        else:
            request.estate = None

        return self.get_response(request)