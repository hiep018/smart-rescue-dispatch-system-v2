# -*- coding: utf-8 -*-
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from portal.models import FirstAidGuide

# Map keyword patterns to image filenames
image_map = [
    ('cam mau', 'first_aid_images/first_aid_bleeding.png'),
    ('chay mau', 'first_aid_images/first_aid_bleeding.png'),
    ('bong', 'first_aid_images/first_aid_burn.png'),
    ('gay xuong', 'first_aid_images/first_aid_fracture.png'),
    ('bong goi', 'first_aid_images/first_aid_fracture.png'),
    ('dot quy', 'first_aid_images/first_aid_bleeding.png'),
    ('phong rop', 'first_aid_images/first_aid_burn.png'),
    ('chan thuong dau', 'first_aid_images/first_aid_head_trauma.png'),
    ('chan thuong so nao', 'first_aid_images/first_aid_head_trauma.png'),
    ('ngo doc', 'first_aid_images/first_aid_food_poisoning.png'),
    ('ong dot', 'first_aid_images/first_aid_bee_sting.png'),
    ('con trung', 'first_aid_images/first_aid_bee_sting.png'),
    ('say nang', 'first_aid_images/first_aid_heat_stroke.png'),
    ('say nong', 'first_aid_images/first_aid_heat_stroke.png'),
    ('bat tinh', 'first_aid_images/first_aid_cpr.png'),
    ('ngung tho', 'first_aid_images/first_aid_cpr.png'),
    ('cpr', 'first_aid_images/first_aid_cpr.png'),
]

guides = FirstAidGuide.objects.all()
updated = 0
for guide in guides:
    kw = guide.keywords.lower() if guide.keywords else ''
    matched_image = None
    for keyword, img_path in image_map:
        if keyword in kw or keyword in guide.title.lower():
            matched_image = img_path
            break
    if matched_image and not guide.image_illustration:
        guide.image_illustration = matched_image
        guide.save()
        updated += 1
        print(f'Updated guide #{guide.id} -> {matched_image}')

print(f'Total updated: {updated}')
for g in FirstAidGuide.objects.all():
    img = g.image_illustration or 'NO IMAGE'
    print(f'  #{g.id}: {img}')
