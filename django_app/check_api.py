import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from portal.views import call_gemini_api

result = call_gemini_api('food poisoning nausea vomiting')
if result:
    print('AI SUCCESS')
    print('Title:', result.get('title', 'N/A').encode('ascii', 'replace').decode())
    steps = result.get('steps', [])
    print(f'Steps count: {len(steps)}')
    print('Severe:', result.get('is_severe', False))
    print('Image:', result.get('image_suggestion', 'none'))
else:
    print('FAIL - Gemini returned None')
