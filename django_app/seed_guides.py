# -*- coding: utf-8 -*-
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from portal.models import FirstAidGuide

guides = [
    {
        'title': 'Hướng dẫn sơ cứu chấn thương đầu / Sọ não',
        'keywords': 'chan thuong dau, chan thuong so nao, dap dau, vo dau, head injury, chan thuong, dau',
        'steps': (
            'Gọi ngay Cấp cứu 115 nếu nạn nhân bất tỉnh, nôn mửa liên tục, co giật hoặc chảy máu tai/mũi.\n'
            'Giữ nạn nhân nằm yên, tránh di chuyển đột ngột, đặc biệt không xoay vặn cổ.\n'
            'Nếu nạn nhân tỉnh táo, đặt nằm nghiêng (tư thế hồi sức) để tránh sặc nếu nôn.\n'
            'Chườm đá bọc trong khăn lên vùng sưng để giảm đau và phù nề.\n'
            'Theo dõi liên tục: mất ý thức, giãn đồng tử một bên, co giật - cần cấp cứu ngay.'
        )
    },
    {
        'title': 'Hướng dẫn sơ cứu ngộ độc thức ăn',
        'keywords': 'ngo doc thuc an, ngo doc, ngo doc thuc pham, non mua, tieu chay, food poisoning',
        'steps': (
            'Cho nạn nhân uống nhiều nước để bù nước và điện giải bị mất do nôn và tiêu chảy.\n'
            'Tuyệt đối không tự ý gây nôn nếu nạn nhân đã bất tỉnh hoặc bị co giật.\n'
            'Nghỉ ngơi hoàn toàn, tránh ăn thức ăn cứng cho đến khi hết nôn ít nhất 4-6 giờ.\n'
            'Có thể dùng oresol (Pedialyte) để bù điện giải sau khi nôn.\n'
            'Gọi ngay 115 nếu triệu chứng không giảm sau 24 giờ hoặc có dấu hiệu mất nước nặng.'
        )
    },
    {
        'title': 'Hướng dẫn sơ cứu ong đốt / côn trùng cắn',
        'keywords': 'ong dot, con trung can, ong vang, ong bap cay, bee sting, insect bite',
        'steps': (
            'Dùng thẻ cứng (thẻ ngân hàng) gạt nhẹ vòi châm ra khỏi da, tránh dùng nhíp kẹp.\n'
            'Rửa sạch vết đốt bằng xà phòng và nước sạch, sau đó chườm đá để giảm sưng đau.\n'
            'Nếu bị ong đốt nhiều hơn 10 mũi hoặc đốt vào vùng cổ/họng, gọi ngay 115 khẩn cấp.\n'
            'Theo dõi phản ứng dị ứng trong 30 phút: khó thở, sưng phù toàn thân, chóng mặt.\n'
            'Nếu có dấu hiệu sốc phản vệ (khó thở, tụt huyết áp), tiêm adrenaline (Epipen) nếu có và gọi cấp cứu ngay.'
        )
    },
    {
        'title': 'Hướng dẫn sơ cứu say nắng / say nóng',
        'keywords': 'say nang, say nong, cam nang, heat stroke, sot cao, cao nhiet',
        'steps': (
            'Di chuyển nạn nhân ra khỏi nơi nắng nóng vào chỗ mát, thoáng gió ngay lập tức.\n'
            'Cởi bớt quần áo, dùng khăn ướt lạnh đặt lên trán, nách, bẹn để hạ nhiệt nhanh.\n'
            'Nếu nạn nhân tỉnh táo, cho uống nước mát hoặc nước oresol từng ngụm nhỏ.\n'
            'Gọi ngay 115 nếu nhiệt độ cơ thể trên 40°C, bất tỉnh, hoặc co giật.\n'
            'Không cho uống nước nếu nạn nhân bất tỉnh hoặc co giật vì có thể bị sặc.'
        )
    },
    {
        'title': 'Hướng dẫn sơ cứu bất tỉnh / ngừng thở (CPR)',
        'keywords': 'bat tinh, ngung tho, ngung tim, hoi suc, cpr, tim mat, ngat',
        'steps': (
            '🚨 CẢNH BÁO NGUY HIỂM: Gọi ngay 115 trước khi thực hiện bất kỳ thao tác nào!\n'
            'Kiểm tra ý thức: lay gọi nhẹ, nếu không phản hồi, gọi người xung quanh hỗ trợ.\n'
            'Đặt nạn nhân nằm ngửa trên mặt phẳng cứng, kiểm tra đường thở và nhịp thở.\n'
            'Thực hiện ép tim ngoài lồng ngực: ép 30 lần liên tục giữa ngực (tần suất 100-120 lần/phút).\n'
            'Thổi ngạt: nghiêng đầu nạn nhân, nâng cằm, bịt mũi và thổi 2 hơi vào miệng sau mỗi 30 lần ép.'
        )
    },
]

for g in guides:
    obj, created = FirstAidGuide.objects.update_or_create(
        title=g['title'],
        defaults={
            'keywords': g['keywords'],
            'steps_instructions': g['steps']
        }
    )
    status = 'Created' if created else 'Updated'
    print(f'{status}: guide #{obj.id}')

total = FirstAidGuide.objects.count()
print(f'Done! Total guides: {total}')
