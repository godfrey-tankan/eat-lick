import json
def summarize_with_gemini(report_data: dict, report_type: str) -> str:
    import google.generativeai as genai
    from django.conf import settings
    import json

    # Configure Gemini
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # Use stateless model call (no chat)
    model = genai.GenerativeModel('gemini-2.0-flash')  # or 'gemini-pro' if needed

    prompt = f"""
    Please summarize this {report_type} ticket report in a short, comprehensive, and non-technical way.
    Include key metrics, insights, trends, and potential concerns or anomalies.

    Report data:
    {json.dumps(report_data, indent=2, default=str)}
    """

    try:
        response = model.generate_content(prompt)  # Stateless call
        return response.text
    except Exception as e:
        return "An error occurred during summarization."