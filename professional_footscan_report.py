#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import PyPDF2
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak
)
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import matplotlib.pyplot as plt
import os
from PIL import Image as PILImage, ImageDraw, ImageFont
import matplotlib
import sys
import json
import glob

matplotlib.use('Agg')

# ============================================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# ============================================================================

WHITE = colors.white
BG_LIGHT = colors.HexColor('#F8F9FA')
TEXT_DARK = colors.HexColor('#1F2933')
TEXT_DARK_HEX = '#1F2933'
TEXT_MUTED = colors.HexColor('#6C757D')
TEXT_MUTED_HEX = '#6C757D'
PRIMARY_BLUE = colors.HexColor('#2E86AB')
PRIMARY_BLUE_HEX = '#2E86AB'
PRIMARY_DARK = colors.HexColor('#1B5E6E')
PRIMARY_DARK_HEX = '#1B5E6E'
SECONDARY_COLOR = colors.HexColor('#F18F01')
SECONDARY_COLOR_HEX = '#F18F01'
HIGH_RISK = colors.HexColor('#DC3545')
HIGH_RISK_HEX = '#DC3545'
MED_RISK = colors.HexColor('#FD7E14')
MED_RISK_HEX = '#FD7E14'
LOW_RISK = colors.HexColor('#28A745')
LOW_RISK_HEX = '#28A745'
NEUTRAL = colors.HexColor('#6C757D')
NEUTRAL_HEX = '#6C757D'
BORDER_COLOR = colors.HexColor('#DEE2E6')
BORDER_COLOR_HEX = '#DEE2E6'
LIGHT_BLUE_BG = colors.HexColor('#E8F4F8')
LIGHT_BLUE_BG_HEX = '#E8F4F8'

MATPLOT_PRIMARY = '#2E86AB'
MATPLOT_SECONDARY = '#F18F01'


# ============================================================================
# 1. РЕГИСТРАЦИЯ ШРИФТОВ
# ============================================================================

def register_fonts():
    """Регистрирует кириллические шрифты"""
    font_paths = [
        "DejaVuSans.ttf",
        "fonts/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/DejaVuSans.ttf",
        "/System/Library/Fonts/DejaVuSans.ttf",
        "C:/Windows/Fonts/dejavusans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/arial.ttf"
    ]

    if sys.platform == 'darwin':
        mac_font_paths = [
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial Unicode.ttf"
        ]
        for path in mac_font_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('Arial', path))
                    pdfmetrics.registerFont(TTFont('Arial-Bold', path))
                    return 'Arial', 'Arial-Bold'
                except Exception:
                    pass

    for path in font_paths:
        if os.path.exists(path):
            try:
                font_name = 'DejaVuSans'
                if 'arial' in path.lower():
                    font_name = 'Arial'

                pdfmetrics.registerFont(TTFont(font_name, path))

                bold_font_name = font_name + '-Bold'
                if os.path.exists(bold_font_name):
                    pdfmetrics.registerFont(TTFont(bold_font_name, bold_font_name))
                else:
                    bold_font_name = font_name

                return font_name, bold_font_name

            except Exception:
                continue

    return 'Helvetica', 'Helvetica-Bold'


# ============================================================================
# 2. СОЗДАНИЕ СТИЛЕЙ
# ============================================================================

def create_styles(normal_font, bold_font):
    """Создаёт стили ParagraphStyle"""
    styles = getSampleStyleSheet()

    styles['Normal'].fontName = normal_font
    styles['Normal'].fontSize = 10
    styles['Normal'].textColor = TEXT_DARK
    styles['Normal'].leading = 14
    styles['Normal'].alignment = TA_JUSTIFY

    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=24,
        textColor=PRIMARY_DARK,
        alignment=TA_CENTER,
        spaceAfter=30,
        spaceBefore=20
    ))

    styles.add(ParagraphStyle(
        name='CompanyTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=22,
        textColor=PRIMARY_DARK,
        alignment=TA_CENTER,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=16,
        textColor=PRIMARY_DARK,
        spaceBefore=25,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=13,
        textColor=PRIMARY_BLUE,
        spaceBefore=15,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name='Important',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=11,
        textColor=TEXT_DARK,
        backColor=LIGHT_BLUE_BG,
        borderPadding=5,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name='BoxedText',
        parent=styles['Normal'],
        fontSize=10,
        backColor=BG_LIGHT,
        borderColor=BORDER_COLOR,
        borderWidth=1,
        borderPadding=10,
        leading=14
    ))

    styles.add(ParagraphStyle(
        name='Small',
        parent=styles['Normal'],
        fontSize=9,
        textColor=TEXT_MUTED,
        leading=12
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=10,
        textColor=WHITE,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='LeftAlign',
        parent=styles['Normal'],
        alignment=TA_LEFT
    ))

    return styles


# ============================================================================
# 3. СОЗДАНИЕ ЛОГОТИПА
# ============================================================================

def create_logo():
    """Создает логотип"""
    logo_path = "logo_footscan.png"

    if not os.path.exists(logo_path):
        try:
            size = 200
            img = PILImage.new('RGB', (size, size), color='white')
            draw = ImageDraw.Draw(img)

            foot_points = [
                (60, 100),
                (90, 50),
                (120, 30),
                (150, 40),
                (160, 80),
                (140, 120),
                (100, 130),
                (60, 100)
            ]

            draw.polygon(foot_points, outline='#2E86AB', fill='#E8F4F8', width=3)

            try:
                font_paths = [
                    "/Library/Fonts/Arial Bold.ttf",
                    "/System/Library/Fonts/Arial.ttf",
                    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                    "Arial.ttf"
                ]
                font = None
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            font = ImageFont.truetype(font_path, 36)
                            break
                        except:
                            continue

                if font is None:
                    try:
                        font = ImageFont.truetype("Arial.ttf", 36)
                    except:
                        font = ImageFont.load_default()
                        font.size = 36

            except:
                font = ImageFont.load_default()

            text_lines = ["FootScan", "Analytics"]
            y_position = 150
            line_height = 40

            for i, line in enumerate(text_lines):
                if hasattr(font, 'getbbox'):
                    bbox = font.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                else:
                    text_width = len(line) * 20

                x = (size - text_width) // 2
                y = y_position + (i * line_height)

                draw.text((x, y), line, fill='#2E86AB', font=font)

            draw.line([(size // 2 - 50, 190), (size // 2 + 50, 190)], fill='#2E86AB', width=2)

            img.save(logo_path, 'PNG', quality=95)
            print(f"[SUCCESS] Логотип создан: {logo_path}")

        except Exception as e:
            print(f"[ERROR] Ошибка создания логотипа: {e}")
            img = PILImage.new('RGB', (100, 100), color=(46, 134, 171))
            draw = ImageDraw.Draw(img)
            draw.text((10, 40), "FSA", fill='white')
            img.save(logo_path, 'PNG')

    return logo_path


# ============================================================================
# 4. ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ PDF
# ============================================================================

def extract_data_from_pdf(pdf_path):
    """Извлекает данные ТОЛЬКО из PDF файла с учетом структуры таблиц"""
    print(f"\n{'=' * 60}")
    print(f"📄 ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ: {os.path.basename(pdf_path)}")
    print('=' * 60)

    data = {
        'client_name': '',
        'foot_length': {'left': 0, 'right': 0},
        'foot_width': {'left': 0, 'right': 0},
        'ball_girth': {'left': 0, 'right': 0},
        'arch_index': {'left': 0, 'right': 0},
        'heel_angle': {'left': 0, 'right': 0},
        'hallux_angle': {'left': 0, 'right': 0},
        'shoe_size': {'left': 0, 'right': 0},
        'shoe_width': '',
        'toe_type': '',
        'gender': '',
        'scan_date': '',
        'scanner_id': '',
        'notes': '',
        'age': '',
        'shop_name': ''
    }

    if not pdf_path or not os.path.exists(pdf_path):
        print("[ERROR] Файл PDF не найден!")
        return data

    try:
        # Чтение PDF
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"[INFO] PDF содержит {len(reader.pages)} страниц")

            all_text = ""
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                text = re.sub(r'\s+', ' ', text)
                all_text += text + "\n"

        # Сохраняем для отладки
        debug_dir = "extracted_data_debug"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)

        safe_filename = os.path.basename(pdf_path).replace('.pdf', '')
        debug_path = os.path.join(debug_dir, f"{safe_filename}_extracted.txt")
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ДЕБАГ ИЗВЛЕЧЕНИЯ: {pdf_path}\n")
            f.write("=" * 80 + "\n\n")
            f.write(all_text)

        print(f"[DEBUG] Текст сохранен в: {debug_path}")

        # ========== ИЗВЛЕЧЕНИЕ ИМЕНИ ==========
        print("\n[INFO] Поиск имени пациента...")

        lines = all_text.split('\n')

        # Стратегия 1: Ищем заголовок с #
        for line in lines[:20]:
            clean_line = line.strip()
            if clean_line.startswith('# ') and len(clean_line) > 2:
                name = clean_line[2:].strip()
                if (len(name) > 2 and
                        not any(keyword in name.lower() for keyword in
                                ['snapshot', 'foot', 'length', 'width', 'scan', 'report', 'page']) and
                        re.search(r'[а-яА-ЯёЁa-zA-Z]{2,}', name)):
                    data['client_name'] = name
                    print(f"[FOUND] Имя из заголовка: {data['client_name']}")
                    break

        # Стратегия 2: Ищем имя в первых строках
        if not data['client_name']:
            for line in lines[:10]:
                clean_line = line.strip()
                if (len(clean_line) > 2 and
                        not re.match(r'^\W*$', clean_line) and  # Не только символы
                        not re.match(r'^\d+\.?\d*$', clean_line) and  # Не число
                        not any(term in clean_line.lower() for term in
                                ['left', 'right', 'foot', 'length', 'width', 'girth', 'snapshot',
                                 'scan', 'date', 'scanner', 'gender', 'male', 'female']) and
                        re.search(r'[а-яА-ЯёЁa-zA-Z]{2,}', clean_line)):

                    # Проверяем, что это не тип стопы
                    if not any(toe_type in clean_line.lower() for toe_type in
                               ['египетский', 'римский', 'греческий', 'квадратный',
                                'egyptian', 'roman', 'greek', 'square']):
                        data['client_name'] = clean_line
                        print(f"[FOUND] Имя из текста: {data['client_name']}")
                        break

        # Стратегия 3: Из имени файла
        if not data['client_name']:
            file_name = os.path.basename(pdf_path)
            name = file_name.replace('_Report.pdf', '').replace('.pdf', '')
            name = re.sub(r'_\d+_\d+', '', name)
            name = name.replace('_', ' ').strip()

            if name and re.search(r'[а-яА-ЯёЁa-zA-Z]{2,}', name):
                data['client_name'] = name
                print(f"[FOUND] Имя из файла: {data['client_name']}")

        # ========== ИЗВЛЕЧЕНИЕ ВСЕХ ЧИСЕЛ ==========
        print("\n[INFO] Извлечение всех числовых данных...")

        # Находим ВСЕ числа с плавающей точкой
        all_floats = re.findall(r'\d+\.\d+', all_text)
        all_ints = re.findall(r'\b\d+\b', all_text)

        print(f"[INFO] Найдено чисел с точкой: {len(all_floats)}")
        print(f"[INFO] Найдено целых чисел: {len(all_ints)}")

        # Выводим первые 20 чисел для анализа
        if all_floats:
            print(f"[DEBUG] Первые 20 чисел с точкой: {all_floats[:20]}")

        # ========== АВТОМАТИЧЕСКИЙ АНАЛИЗ ЧИСЕЛ ==========
        print("\n[INFO] Автоматический анализ числовых данных...")

        # 1. ДЛИНА СТОПЫ - самые большие числа (230-300)
        foot_length_candidates = []
        for num in all_floats:
            val = float(num)
            if 230 <= val <= 300:
                foot_length_candidates.append(val)

        if len(foot_length_candidates) >= 2:
            data['foot_length']['left'] = foot_length_candidates[0]
            data['foot_length']['right'] = foot_length_candidates[1]
            print(f"[FOUND] Длина стопы: Л={foot_length_candidates[0]}, П={foot_length_candidates[1]}")
        elif len(foot_length_candidates) == 1:
            data['foot_length']['left'] = foot_length_candidates[0]
            data['foot_length']['right'] = foot_length_candidates[0] + 1.0
            print(f"[FOUND] Длина стопы (одно значение): {foot_length_candidates[0]}")

        # 2. ШИРИНА СТОПЫ - средние числа (80-120)
        foot_width_candidates = []
        for num in all_floats:
            val = float(num)
            if 80 <= val <= 120:
                foot_width_candidates.append(val)

        if len(foot_width_candidates) >= 2:
            data['foot_width']['left'] = foot_width_candidates[0]
            data['foot_width']['right'] = foot_width_candidates[1]
            print(f"[FOUND] Ширина стопы: Л={foot_width_candidates[0]}, П={foot_width_candidates[1]}")

        # 3. ОБХВАТ ПЛЮСНЫ - средние числа (220-270)
        ball_girth_candidates = []
        for num in all_floats:
            val = float(num)
            if 220 <= val <= 270:
                ball_girth_candidates.append(val)

        if len(ball_girth_candidates) >= 2:
            data['ball_girth']['left'] = ball_girth_candidates[0]
            data['ball_girth']['right'] = ball_girth_candidates[1]
            print(f"[FOUND] Обхват плюсны: Л={ball_girth_candidates[0]}, П={ball_girth_candidates[1]}")

        # 4. ИНДЕКС СВОДА - маленькие числа (0.2-0.4)
        arch_index_candidates = []
        for num in all_floats:
            val = float(num)
            if 0.2 <= val <= 0.4:
                arch_index_candidates.append(val)

        if len(arch_index_candidates) >= 2:
            data['arch_index']['left'] = arch_index_candidates[0]
            data['arch_index']['right'] = arch_index_candidates[1]
            print(f"[FOUND] Индекс свода: Л={arch_index_candidates[0]}, П={arch_index_candidates[1]}")

        # 5. УГОЛЬ ПЯТКИ - маленькие целые числа (0-10)
        heel_angle_candidates = []
        for num in all_ints:
            val = int(num)
            if 0 <= val <= 10:
                heel_angle_candidates.append(val)

        if len(heel_angle_candidates) >= 2:
            data['heel_angle']['left'] = heel_angle_candidates[0]
            data['heel_angle']['right'] = heel_angle_candidates[1]
            print(f"[FOUND] Угол пятки: Л={heel_angle_candidates[0]}, П={heel_angle_candidates[1]}")

        # 6. УГОЛЬ БОЛЬШОГО ПАЛЬЦА - маленькие-средние числа (0-30)
        hallux_angle_candidates = []
        for num in all_floats:
            val = float(num)
            if 0 <= val <= 30:
                hallux_angle_candidates.append(val)

        if len(hallux_angle_candidates) >= 2:
            data['hallux_angle']['left'] = hallux_angle_candidates[0]
            data['hallux_angle']['right'] = hallux_angle_candidates[1]
            print(f"[FOUND] Угол большого пальца: Л={hallux_angle_candidates[0]}, П={hallux_angle_candidates[1]}")

        # 7. РАЗМЕР ОБУВИ - расчет на основе длины
        def calculate_shoe_size(foot_length_mm):
            if foot_length_mm <= 0:
                return 0
            # Формула: EU size = (foot_length_mm * 1.5 + 15.5) / 10
            eu_size = (foot_length_mm * 1.5 + 15.5) / 10
            # Округляем до 0.5
            eu_size = round(eu_size * 2) / 2
            return eu_size

        if data['foot_length']['left'] > 0:
            data['shoe_size']['left'] = calculate_shoe_size(data['foot_length']['left'])

        if data['foot_length']['right'] > 0:
            data['shoe_size']['right'] = calculate_shoe_size(data['foot_length']['right'])

        # Также ищем размер обуви в тексте (35-50)
        shoe_size_candidates = []
        for num in all_floats + all_ints:
            try:
                val = float(num)
                if 35 <= val <= 50:
                    shoe_size_candidates.append(val)
            except:
                continue

        if shoe_size_candidates:
            data['shoe_size']['left'] = shoe_size_candidates[0]
            data['shoe_size']['right'] = shoe_size_candidates[0]
            print(f"[FOUND] Размер обуви в тексте: {shoe_size_candidates[0]}")

        # ========== ТЕКСТОВЫЕ ДАННЫЕ ==========
        print("\n[INFO] Извлечение текстовых данных...")

        # Ширина обуви
        width_match = re.search(r'Shoe Width.*?([A-G])', all_text, re.IGNORECASE)
        if width_match:
            data['shoe_width'] = width_match.group(1)
            print(f"[FOUND] Ширина обуви: {data['shoe_width']}")

        # Тип стопы
        if 'Egyptian' in all_text:
            data['toe_type'] = 'Египетский'
        elif 'Roman' in all_text:
            data['toe_type'] = 'Римский'
        elif 'Greek' in all_text:
            data['toe_type'] = 'Греческий'
        elif 'Square' in all_text:
            data['toe_type'] = 'Квадратный'

        if data['toe_type']:
            print(f"[FOUND] Тип стопы: {data['toe_type']}")

        # Пол
        if 'Male' in all_text or 'мужской' in all_text.lower():
            data['gender'] = 'Мужской'
        elif 'Female' in all_text or 'женский' in all_text.lower():
            data['gender'] = 'Женский'

        if data['gender']:
            print(f"[FOUND] Пол: {data['gender']}")

        # Дата сканирования
        date_match = re.search(r'Scan date\s*(\d{4}/\d{2}/\d{2})', all_text)
        if date_match:
            try:
                date_obj = datetime.strptime(date_match.group(1), '%Y/%m/%d')
                data['scan_date'] = date_obj.strftime('%d.%m.%Y')
                print(f"[FOUND] Дата сканирования: {data['scan_date']}")
            except:
                data['scan_date'] = date_match.group(1)
        else:
            # Ищем любую дату
            date_match = re.search(r'(\d{4}/\d{2}/\d{2})', all_text)
            if date_match:
                data['scan_date'] = date_match.group(1)

        # ID сканера
        scanner_match = re.search(r'Scanner No\s*(\d+_\d+)', all_text)
        if scanner_match:
            data['scanner_id'] = scanner_match.group(1)
            print(f"[FOUND] ID сканера: {data['scanner_id']}")
        else:
            # Из имени файла
            file_base = os.path.basename(pdf_path)
            scanner_match = re.search(r'_(\d+_\d+)_', file_base)
            if scanner_match:
                data['scanner_id'] = scanner_match.group(1)

        # ========== РУЧНОЙ ПОИСК ПО ПАТТЕРНАМ (если автоматический не сработал) ==========
        print(f"\n{'=' * 60}")
        print("📊 ПРОВЕРКА И КОРРЕКЦИЯ ДАННЫХ:")
        print('=' * 60)

        # Если данных недостаточно, используем эвристику
        if data['foot_length']['left'] == 0:
            print("[WARNING] Длина стопы не найдена автоматически!")

            try:
                with open(debug_path, 'r', encoding='utf-8') as f:
                    debug_content = f.read()

                # Ищем конкретные паттерны
                # Паттерн: "Foot Length (mm) 271.7 273.8"
                foot_pattern = r'Foot Length.*?\(mm\).*?(\d+\.\d+).*?(\d+\.\d+)'
                foot_match = re.search(foot_pattern, debug_content, re.IGNORECASE)
                if foot_match:
                    data['foot_length']['left'] = float(foot_match.group(1))
                    data['foot_length']['right'] = float(foot_match.group(2))
                    print(
                        f"[FOUND] Длина стопы (паттерн): Л={data['foot_length']['left']}, П={data['foot_length']['right']}")

                # Паттерн: "Foot Width (mm) 100.2 106.8"
                width_pattern = r'Foot Width.*?\(mm\).*?(\d+\.\d+).*?(\d+\.\d+)'
                width_match = re.search(width_pattern, debug_content, re.IGNORECASE)
                if width_match:
                    data['foot_width']['left'] = float(width_match.group(1))
                    data['foot_width']['right'] = float(width_match.group(2))
                    print(
                        f"[FOUND] Ширина стопы (паттерн): Л={data['foot_width']['left']}, П={data['foot_width']['right']}")

                # Паттерн: "Ball Girth (mm) 238.4 249.2"
                ball_pattern = r'Ball Girth.*?\(mm\).*?(\d+\.\d+).*?(\d+\.\d+)'
                ball_match = re.search(ball_pattern, debug_content, re.IGNORECASE)
                if ball_match:
                    data['ball_girth']['left'] = float(ball_match.group(1))
                    data['ball_girth']['right'] = float(ball_match.group(2))
                    print(
                        f"[FOUND] Обхват плюсны (паттерн): Л={data['ball_girth']['left']}, П={data['ball_girth']['right']}")

                # Паттерн: "Arch Index 0.27 0.37"
                arch_pattern = r'Arch Index.*?(\d+\.\d+).*?(\d+\.\d+)'
                arch_match = re.search(arch_pattern, debug_content, re.IGNORECASE)
                if arch_match:
                    data['arch_index']['left'] = float(arch_match.group(1))
                    data['arch_index']['right'] = float(arch_match.group(2))
                    print(
                        f"[FOUND] Индекс свода (паттерн): Л={data['arch_index']['left']}, П={data['arch_index']['right']}")

                # Паттерн: "Hallux Angle 10.4 16.0"
                hallux_pattern = r'Hallux Angle.*?(\d+\.\d+).*?(\d+\.\d+)'
                hallux_match = re.search(hallux_pattern, debug_content, re.IGNORECASE)
                if hallux_match:
                    data['hallux_angle']['left'] = float(hallux_match.group(1))
                    data['hallux_angle']['right'] = float(hallux_match.group(2))
                    print(
                        f"[FOUND] Угол большого пальца (паттерн): Л={data['hallux_angle']['left']}, П={data['hallux_angle']['right']}")

                # Паттерн: "Heel Angle 1 Inv 6 Eve" или "Heel Angle 1 6"
                heel_pattern1 = r'Heel Angle.*?(\d+).*?Inv.*?(\d+).*?Eve'
                heel_pattern2 = r'Heel Angle.*?(\d+).*?(\d+)'

                heel_match = re.search(heel_pattern1, debug_content, re.IGNORECASE)
                if heel_match:
                    data['heel_angle']['left'] = int(heel_match.group(1))
                    data['heel_angle']['right'] = int(heel_match.group(2))
                else:
                    heel_match = re.search(heel_pattern2, debug_content, re.IGNORECASE)
                    if heel_match:
                        data['heel_angle']['left'] = int(heel_match.group(1))
                        data['heel_angle']['right'] = int(heel_match.group(2))

                if data['heel_angle']['left'] > 0:
                    print(
                        f"[FOUND] Угол пятки (паттерн): Л={data['heel_angle']['left']}, П={data['heel_angle']['right']}")

            except Exception as e:
                print(f"[ERROR] Ошибка при ручном анализе: {e}")

        # ========== ВЫВОД РЕЗУЛЬТАТОВ ==========
        print(f"\n{'=' * 60}")
        print("📊 ИТОГОВЫЕ ИЗВЛЕЧЕННЫЕ ДАННЫЕ:")
        print('=' * 60)

        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{key}: Л={value['left']}, П={value['right']}")
            else:
                print(f"{key}: {value}")

        # Сохраняем в JSON
        json_path = os.path.join(debug_dir, f"{safe_filename}_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Данные сохранены в JSON: {json_path}")

        # Проверяем, достаточно ли данных для генерации отчета
        if data['foot_length']['left'] == 0:
            print(f"\n[ERROR] Не удалось извлечь основные данные!")
        else:
            print(f"\n[SUCCESS] Данные успешно извлечены!")

    except Exception as e:
        print(f"[ERROR] Ошибка чтения PDF: {e}")
        import traceback
        traceback.print_exc()

        # В случае ошибки - данные из имени файла
        file_name = os.path.basename(pdf_path)
        data['client_name'] = file_name.replace('_Report.pdf', '').replace('_', ' ')
        data['scan_date'] = datetime.now().strftime('%d.%m.%Y')

    return data

# ============================================================================
# 5. РАСЧЕТ РИСКОВ И РЕКОМЕНДАЦИЙ
# ============================================================================

def calculate_risk_scores(data):
    """Рассчитывает риски на основе данных"""
    print(f"\n{'=' * 60}")
    print("⚖️ РАСЧЕТ РИСКОВ")
    print('=' * 60)

    scores = {
        'degenerative': 20,
        'spinal': 20,
        'traumatic': 20,
        'comfort': 20,
        'progression': 20
    }

    # Анализ индекса свода
    avg_arch = (data['arch_index']['left'] + data['arch_index']['right']) / 2
    arch_status = ""

    if avg_arch < 0.26:
        scores['degenerative'] += 25
        scores['spinal'] += 20
        arch_status = "Высокий свод стопы (полая стопа)"
        print(f"  ⚠️ {arch_status}: {avg_arch:.3f}")
    elif avg_arch > 0.29:
        scores['traumatic'] += 20
        scores['comfort'] += 15
        arch_status = "Низкий свод стопы (плоскостопие)"
        print(f"  ⚠️ {arch_status}: {avg_arch:.3f}")
    else:
        arch_status = "Нормальный свод стопы"
        print(f"  ✓ {arch_status}: {avg_arch:.3f}")

    # Асимметрия длины
    length_diff = abs(data['foot_length']['left'] - data['foot_length']['right'])
    if length_diff > 3:
        scores['spinal'] += 15
        scores['progression'] += 10
        print(f"  ⚠️ Асимметрия длины: {length_diff:.1f} мм")
    else:
        print(f"  ✓ Симметрия длины: {length_diff:.1f} мм")

    # Асимметрия ширины
    width_diff = abs(data['foot_width']['left'] - data['foot_width']['right'])
    if width_diff > 2:
        scores['comfort'] += 15
        print(f"  ⚠️ Асимметрия ширины: {width_diff:.1f} мм")
    else:
        print(f"  ✓ Симметрия ширины: {width_diff:.1f} мм")

    # Угол пятки
    heel_issues = []
    for side in ['left', 'right']:
        angle = data['heel_angle'][side]
        side_name = 'Левая' if side == 'left' else 'Правая'
        if abs(angle) > 4:
            scores['traumatic'] += 10
            scores['comfort'] += 8
            heel_issues.append(f"{side_name} пятка: {angle}°")

    if heel_issues:
        print(f"  ⚠️ Отклонения пятки: {', '.join(heel_issues)}")
    else:
        print(f"  ✓ Нормальный угол пятки")

    # Угол большого пальца
    hallux_issues = []
    for side in ['left', 'right']:
        angle = data['hallux_angle'][side]
        side_name = 'Левая' if side == 'left' else 'Правая'
        if angle > 15:
            scores['degenerative'] += 20
            scores['comfort'] += 15
            hallux_issues.append(f"{side_name} стопа: {angle}° (выраженный)")
        elif angle > 8:
            scores['degenerative'] += 10
            scores['comfort'] += 8
            hallux_issues.append(f"{side_name} стопа: {angle}° (умеренный)")

    if hallux_issues:
        print(f"  ⚠️ Вальгусная деформация: {', '.join(hallux_issues)}")
    else:
        print(f"  ✓ Нормальный угол большого пальца")

    # Нормализация баллов
    for key in scores:
        scores[key] = max(0, min(100, scores[key]))

    # Определение уровня риска
    for name, score in scores.items():
        if score >= 70:
            level = "ВЫСОКИЙ"
            emoji = "🔴"
        elif score >= 50:
            level = "ПОВЫШЕННЫЙ"
            emoji = "🟡"
        else:
            level = "НОРМА"
            emoji = "🟢"

        print(f"  {emoji} {name}: {score}/100 ({level})")

    # Генерация рекомендаций
    recommendations = generate_recommendations(data, scores, arch_status)

    return scores, recommendations


def generate_recommendations(data, risk_scores, arch_status):
    """Генерирует персонализированные рекомендации"""
    recommendations = []

    # 1. Общие рекомендации на основе типа стопы
    if "Высокий свод" in arch_status:
        recommendations.append({
            "title": "👟 Обувь для высокого свода",
            "description": "Рекомендуется обувь с дополнительной амортизацией и мягкой стелькой. Ищите модели с маркировкой 'Neutral Cushioning' или 'High Arch Support'. Избегайте жесткой обуви с плоской подошвой.",
            "priority": "high"
        })
    elif "Низкий свод" in arch_status:
        recommendations.append({
            "title": "👟 Обувь для плоскостопия",
            "description": "Требуется обувь с поддержкой свода и стабилизацией. Ищите модели с маркировкой 'Stability' или 'Motion Control'. Обязательны ортопедические стельки с супинатором.",
            "priority": "high"
        })
    else:
        recommendations.append({
            "title": "👟 Стандартная обувь",
            "description": "Подходит большинство типов обуви. Рекомендуются модели с умеренной поддержкой свода и амортизацией.",
            "priority": "medium"
        })

    # 2. Рекомендации по размеру и ширине
    if data['shoe_width']:
        recommendations.append({
            "title": "📏 Ширина обуви",
            "description": f"Ваш размер: {data['shoe_size']['left']} EU. Рекомендуемая ширина: {data['shoe_width']}.",
            "priority": "medium"
        })

    # 3. Рекомендации по углу пятки
    if any(abs(angle) > 4 for angle in [data['heel_angle']['left'], data['heel_angle']['right']]):
        recommendations.append({
            "title": "🦶 Коррекция положения пятки",
            "description": "При отклонениях пятки рекомендуются упражнения на укрепление мышц голеностопа и индивидуальные ортопедические стельки с коррекцией заднего отдела.",
            "priority": "medium"
        })

    # 4. Рекомендации при вальгусной деформации
    if any(angle > 8 for angle in [data['hallux_angle']['left'], data['hallux_angle']['right']]):
        hallux_max = max(data['hallux_angle']['left'], data['hallux_angle']['right'])
        severity = "выраженной" if hallux_max > 15 else "умеренной"
        recommendations.append({
            "title": "🦶 Профилактика Hallux Valgus",
            "description": f"При {severity} вальгусной деформации ({hallux_max}°) рекомендуется: обувь с широким мысом, разделители для пальцев, упражнения для укрепления мышц стопы.",
            "priority": "high"
        })

    # 5. Рекомендации по асимметрии
    length_diff = abs(data['foot_length']['left'] - data['foot_length']['right'])
    width_diff = abs(data['foot_width']['left'] - data['foot_width']['right'])

    if length_diff > 3 or width_diff > 2:
        recommendations.append({
            "title": "⚖️ Коррекция асимметрии",
            "description": f"Заметная асимметрия стоп (длина: {length_diff:.1f} мм, ширина: {width_diff:.1f} мм). Рекомендуется: индивидуальные стельки для каждой стопы, контроль осанки, консультация ортопеда.",
            "priority": "medium"
        })

    # 6. Общие рекомендации
    recommendations.append({
        "title": "🏃 Упражнения для стоп",
        "description": "Ежедневные упражнения: катание мячика стопой, подъем на носки, растяжка икроножных мышц. Ходьба босиком по неровным поверхностям (песок, трава).",
        "priority": "low"
    })

    recommendations.append({
        "title": "🩺 Регулярное наблюдение",
        "description": f"Повторное обследование через 6-12 месяцев. При появлении болей или дискомфорта - консультация врача-ортопеда. ID вашего скана: {data['scanner_id']}",
        "priority": "low"
    })

    # Сортируем по приоритету
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    recommendations.sort(key=lambda x: priority_order[x['priority']])

    return recommendations


# ============================================================================
# 6. СОЗДАНИЕ ГРАФИКОВ
# ============================================================================

def create_radar_chart(risk_scores, output_path):
    """Создает радарную диаграмму рисков"""
    try:
        plt.rcParams.update({
            'font.family': 'Arial',
            'axes.unicode_minus': False,
            'figure.autolayout': True,
            'savefig.dpi': 150
        })

        categories = ['Дегенеративный\n(суставы)', 'Позвоночный\n(осанка)',
                      'Травматический\n(риск травм)', 'Комфорт\n(обувь)',
                      'Прогрессия\n(деформация)']

        values = [risk_scores['degenerative'], risk_scores['spinal'],
                  risk_scores['traumatic'], risk_scores['comfort'],
                  risk_scores['progression']]

        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        values += values[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=9, color=TEXT_DARK_HEX)

        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_yticklabels(['0', '25', '50', '75', '100'], fontsize=8, color=TEXT_MUTED_HEX)
        ax.grid(True, alpha=0.3, color=BORDER_COLOR_HEX, linestyle='--', linewidth=0.5)

        ax.fill_between(angles, 0, 40, color=LOW_RISK_HEX, alpha=0.1)
        ax.fill_between(angles, 40, 70, color=MED_RISK_HEX, alpha=0.1)
        ax.fill_between(angles, 70, 100, color=HIGH_RISK_HEX, alpha=0.1)

        ax.plot(angles, [40] * len(angles), color=LOW_RISK_HEX, alpha=0.5, linewidth=0.5)
        ax.plot(angles, [70] * len(angles), color=MED_RISK_HEX, alpha=0.5, linewidth=0.5)

        ax.plot(angles, values, 'o-', linewidth=2, color=MATPLOT_PRIMARY,
                markersize=6, markerfacecolor='white', markeredgewidth=1.5)
        ax.fill(angles, values, alpha=0.15, color=MATPLOT_PRIMARY)

        for angle, value in zip(angles[:-1], values[:-1]):
            ax.text(angle, value + 4, f'{value:.0f}',
                    ha='center', va='center', fontsize=7, fontweight='bold')

        plt.title('Профиль биомеханических рисков', size=12, pad=20, fontweight='bold', color=PRIMARY_DARK_HEX)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"[GRAPH] Радарная диаграмма сохранена: {output_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Ошибка создания радарной диаграммы: {e}")
        return False


def create_comparison_chart(data, output_path):
    """Создает сравнительную диаграмму параметров стоп"""
    try:
        plt.rcParams.update({
            'font.family': 'Arial',
            'axes.unicode_minus': False,
            'figure.autolayout': True
        })

        categories = ['Длина\nстопы, мм', 'Ширина\nстопы, мм',
                      'Индекс\nсвода (×100)', 'Угол\nпятки, °', 'Угол\nпальца, °']

        left_values = [
            data['foot_length']['left'],
            data['foot_width']['left'],
            data['arch_index']['left'] * 100,
            data['heel_angle']['left'],
            data['hallux_angle']['left']
        ]

        right_values = [
            data['foot_length']['right'],
            data['foot_width']['right'],
            data['arch_index']['right'] * 100,
            data['heel_angle']['right'],
            data['hallux_angle']['right']
        ]

        x = np.arange(len(categories))
        width = 0.35

        fig, ax = plt.subplots(figsize=(9, 5))

        bars_left = ax.bar(x - width / 2, left_values, width,
                           label='Левая стопа', color=MATPLOT_PRIMARY, alpha=0.85,
                           edgecolor='white', linewidth=1)

        bars_right = ax.bar(x + width / 2, right_values, width,
                            label='Правая стопа', color=MATPLOT_SECONDARY, alpha=0.85,
                            edgecolor='white', linewidth=1)

        ax.set_ylabel('Значение', fontsize=10, fontweight='bold')
        ax.set_title('Сравнительный анализ стоп', fontsize=12, fontweight='bold',
                     pad=15, color=PRIMARY_DARK_HEX)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=9, color=TEXT_DARK_HEX)
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.2, axis='y', linestyle='--')
        ax.set_axisbelow(True)

        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, height,
                        f'{height:.1f}', ha='center', va='bottom',
                        fontsize=8, fontweight='bold')

        autolabel(bars_left)
        autolabel(bars_right)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"[GRAPH] Сравнительная диаграмма сохранена: {output_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Ошибка создания сравнительной диаграммы: {e}")
        return False


# ============================================================================
# 7. ГЕНЕРАЦИЯ PDF ОТЧЕТА
# ============================================================================

def create_pdf_report(data, risk_scores, recommendations, output_filename):
    """Создает профессиональный PDF отчет"""
    print(f"\n{'=' * 60}")
    print("📄 СОЗДАНИЕ PDF ОТЧЕТА")
    print('=' * 60)

    normal_font, bold_font = register_fonts()
    styles = create_styles(normal_font, bold_font)

    temp_dir = "temp_graphs"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)

    print("[1/6] Создание графиков...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    radar_chart_path = os.path.join(temp_dir, f"radar_chart_{timestamp}.png")
    comparison_chart_path = os.path.join(temp_dir, f"comparison_chart_{timestamp}.png")

    radar_created = create_radar_chart(risk_scores, radar_chart_path)
    comparison_created = create_comparison_chart(data, comparison_chart_path)

    logo_path = create_logo()

    print("[2/6] Настройка документа...")
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        title=f"FootScan Analytics - Отчет для {data['client_name']}",
        author="FootScan Analytics",
        creator="FootScan Analytics System"
    )

    story = []

    # ==================== ТИТУЛЬНАЯ СТРАНИЦА ====================
    print("[3/6] Формирование титульной страницы...")

    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=4 * cm, height=4 * cm)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.5 * cm))
        except Exception:
            pass

    story.append(Paragraph("FootScan Analytics", styles['CompanyTitle']))
    story.append(Paragraph("Цифровая лаборатория здоровья стоп",
                           ParagraphStyle(name='CompanySubtitle', parent=styles['Normal'],
                                          fontSize=11, textColor=TEXT_MUTED,
                                          alignment=TA_CENTER, spaceAfter=20)))

    story.append(Spacer(1, 1.2 * cm))

    story.append(Paragraph("ПЕРСОНАЛИЗИРОВАННЫЙ ОТЧЕТ", styles['ReportTitle']))
    story.append(Paragraph("Биомеханический анализ стоп",
                           ParagraphStyle(name='ReportSubtitle', parent=styles['Normal'],
                                          alignment=TA_CENTER, spaceAfter=15)))

    story.append(Spacer(1, 1.5 * cm))

    patient_info = [
        [Paragraph(f"<font name='{bold_font}'><b>Пациент</b></font>", styles['Important']),
         Paragraph(f"<font name='{normal_font}'>{data['client_name']}</font>", styles['Normal'])],
        [Paragraph(f"<font name='{bold_font}'><b>Пол</b></font>", styles['Important']),
         Paragraph(f"<font name='{normal_font}'>{data['gender']}</font>", styles['Normal'])],
        [Paragraph(f"<font name='{bold_font}'><b>Дата обследования</b></font>", styles['Important']),
         Paragraph(f"<font name='{normal_font}'>{data['scan_date']}</font>", styles['Normal'])],
        [Paragraph(f"<font name='{bold_font}'><b>ID отчета</b></font>", styles['Important']),
         Paragraph(f"<font name='{normal_font}'>FSA-{datetime.now().strftime('%Y%m%d%H%M')}</font>", styles['Normal'])],
        [Paragraph(f"<font name='{bold_font}'><b>Сканер</b></font>", styles['Important']),
         Paragraph(f"<font name='{normal_font}'>{data['scanner_id']}</font>", styles['Normal'])],
    ]

    patient_table = Table(patient_info, colWidths=[4 * cm, 9 * cm])
    patient_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE_BG),
        ('BOX', (0, 0), (-1, -1), 1, PRIMARY_BLUE),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 10),
        ('RIGHTPADDING', (1, 0), (1, -1), 10),
    ]))

    story.append(patient_table)
    story.append(Spacer(1, 1.8 * cm))

    intro_text = f"""
    <font name='{normal_font}'><b>Данный отчет содержит:</b></font><br/>
    <font name='{normal_font}'>• Детальный анализ биомеханических параметров ваших стоп</font><br/>
    <font name='{normal_font}'>• Оценку индивидуальных рисков для здоровья</font><br/>
    <font name='{normal_font}'>• Персонализированные рекомендации по подбору обуви</font><br/>
    <font name='{normal_font}'>• Советы по поддержанию здоровья стоп и профилактике</font>
    """

    story.append(Paragraph(intro_text, styles['BoxedText']))

    story.append(Spacer(1, 2 * cm))

    story.append(Paragraph(
        f"<font name='{bold_font}'><b>КОНФИДЕНЦИАЛЬНЫЙ МЕДИЦИНСКИЙ ДОКУМЕНТ</b><br/>"
        f"Предназначен только для пациента и лечащего врача</font>",
        ParagraphStyle(
            name='Confidential',
            parent=styles['Normal'],
            fontSize=9,
            textColor=NEUTRAL,
            alignment=TA_CENTER,
            spaceAfter=0
        )
    ))

    story.append(PageBreak())

    # ==================== СТРАНИЦА 2: АНАЛИЗ РИСКОВ ====================
    print("[4/6] Формирование страницы анализа рисков...")

    story.append(Paragraph("1. АНАЛИЗ БИОМЕХАНИЧЕСКИХ РИСКОВ", styles['SectionTitle']))
    story.append(Spacer(1, 0.4 * cm))

    analysis_text = f"""
    <font name='{normal_font}'>На основе анализа параметров ваших стоп, система определила индивидуальный профиль рисков. 
    Уровень риска оценивается по шкале от 0 до 100 баллов, где:</font><br/>
    <font name='{normal_font}'>• <font color="{LOW_RISK_HEX}"><b>0-49</b></font> — низкий риск</font><br/>
    <font name='{normal_font}'>• <font color="{MED_RISK_HEX}"><b>50-69</b></font> — умеренный риск</font><br/>
    <font name='{normal_font}'>• <font color="{HIGH_RISK_HEX}"><b>70-100</b></font> — высокий риск</font><br/>
    <br/>
    <font name='{normal_font}'>Рекомендуется обратить особое внимание на категории с оценкой выше 50 баллов.</font>
    """

    story.append(Paragraph(analysis_text, styles['Normal']))
    story.append(Spacer(1, 0.8 * cm))

    if radar_created and os.path.exists(radar_chart_path):
        try:
            radar_img = Image(radar_chart_path, width=14 * cm, height=14 * cm)
            radar_img.hAlign = 'CENTER'
            story.append(radar_img)
            story.append(Spacer(1, 0.5 * cm))
        except Exception:
            pass

    risk_data = []
    risk_categories_info = [
        ('Дегенеративный риск', 'Риск развития артрозов и дегенеративных изменений суставов',
         risk_scores['degenerative']),
        ('Позвоночный риск', 'Влияение на осанку и здоровье позвоночника',
         risk_scores['spinal']),
        ('Травматический риск', 'Вероятность получения травм при нагрузках',
         risk_scores['traumatic']),
        ('Комфортный риск', 'Сложности с подбором комфортной обуви',
         risk_scores['comfort']),
        ('Риск прогрессирования', 'Вероятность усугубления существующих особенностей',
         risk_scores['progression'])
    ]

    risk_data.append([
        Paragraph(f"<font name='{bold_font}'><b>Категория риска</b></font>", styles['TableHeader']),
        Paragraph(f"<font name='{bold_font}'><b>Оценка</b></font>", styles['TableHeader']),
        Paragraph(f"<font name='{bold_font}'><b>Уровень</b></font>", styles['TableHeader'])
    ])

    for name, description, score in risk_categories_info:
        if score >= 70:
            color = HIGH_RISK
            level = "ВЫСОКИЙ"
        elif score >= 50:
            color = MED_RISK
            level = "УМЕРЕННЫЙ"
        else:
            color = LOW_RISK
            level = "НИЗКИЙ"

        risk_data.append([
            Paragraph(f"<font name='{normal_font}'><b>{name}</b><br/><font size=7>{description}</font></font>",
                      ParagraphStyle(name='RiskDesc', parent=styles['Normal'], fontSize=9)),
            Paragraph(f"<font name='{normal_font}'><b>{score}/100</b></font>",
                      ParagraphStyle(name='RiskScore', parent=styles['Normal'],
                                     fontSize=10, textColor=color, alignment=TA_CENTER)),
            Paragraph(f"<font name='{bold_font}'><b>{level}</b></font>",
                      ParagraphStyle(name='RiskLevel', parent=styles['Normal'],
                                     fontSize=9, textColor=color, alignment=TA_CENTER))
        ])

    risk_table = Table(risk_data, colWidths=[7 * cm, 3 * cm, 3.5 * cm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))

    story.append(risk_table)
    story.append(Spacer(1, 0.8 * cm))

    total_risk = sum(risk_scores.values()) / len(risk_scores)
    if total_risk >= 70:
        overall_risk = "высокий"
        risk_color = HIGH_RISK_HEX
    elif total_risk >= 50:
        overall_risk = "умеренный"
        risk_color = MED_RISK_HEX
    else:
        overall_risk = "низкий"
        risk_color = LOW_RISK_HEX

    overall_text = f"""
    <font name='{normal_font}'><b>Общая оценка:</b> <font color="{risk_color}">{overall_risk.upper()}</font> ({total_risk:.1f}/100)</font><br/>
    <font name='{normal_font}' size='9'>На основе анализа всех параметров стопы</font>
    """

    story.append(Paragraph(overall_text, styles['BoxedText']))

    story.append(PageBreak())

    # ==================== СТРАНИЦА 3: ДЕТАЛЬНЫЙ АНАЛИЗ ====================
    print("[5/6] Формирование страницы детального анализа...")

    story.append(Paragraph("2. ДЕТАЛЬНЫЙ БИОМЕХАНИЧЕСКИЙ АНАЛИЗ", styles['SectionTitle']))
    story.append(Spacer(1, 0.4 * cm))

    if comparison_created and os.path.exists(comparison_chart_path):
        try:
            comp_img = Image(comparison_chart_path, width=15 * cm, height=9 * cm)
            comp_img.hAlign = 'CENTER'
            story.append(comp_img)
            story.append(Spacer(1, 0.5 * cm))
        except Exception:
            pass

    story.append(Paragraph(f"<font name='{bold_font}'><b>Измеренные параметры стоп:</b></font>", styles['SubSection']))

    params_data = [
        [Paragraph(f"<font name='{bold_font}'><b>Параметр</b></font>", styles['TableHeader']),
         Paragraph(f"<font name='{bold_font}'><b>Левая стопа</b></font>", styles['TableHeader']),
         Paragraph(f"<font name='{bold_font}'><b>Правая стопа</b></font>", styles['TableHeader']),
         Paragraph(f"<font name='{bold_font}'><b>Норма</b></font>", styles['TableHeader'])],

        [Paragraph(f"<font name='{normal_font}'>Длина стопы (мм)</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['foot_length']['left']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['foot_length']['right']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>230-260 мм</font>", styles['Normal'])],

        [Paragraph(f"<font name='{normal_font}'>Ширина стопы (мм)</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['foot_width']['left']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['foot_width']['right']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>90-105 мм</font>", styles['Normal'])],

        [Paragraph(f"<font name='{normal_font}'>Обхват плюсны (мм)</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['ball_girth']['left']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['ball_girth']['right']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>230-250 мм</font>", styles['Normal'])],

        [Paragraph(f"<font name='{normal_font}'>Индекс свода</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['arch_index']['left']:.3f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['arch_index']['right']:.3f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>0.26-0.29</font>", styles['Normal'])],

        [Paragraph(f"<font name='{normal_font}'>Угол пятки (°)</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['heel_angle']['left']}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['heel_angle']['right']}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>0-4°</font>", styles['Normal'])],

        [Paragraph(f"<font name='{normal_font}'>Угол пальца (°)</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['hallux_angle']['left']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['hallux_angle']['right']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>0-8°</font>", styles['Normal'])],

        [Paragraph(f"<font name='{normal_font}'>Размер обуви (EU)</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['shoe_size']['left']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['shoe_size']['right']:.1f}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>По измерениям</font>", styles['Normal'])],

        [Paragraph(f"<font name='{normal_font}'>Тип стопы</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['toe_type']}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>{data['toe_type']}</font>", styles['Normal']),
         Paragraph(f"<font name='{normal_font}'>-</font>", styles['Normal'])],
    ]

    params_table = Table(params_data, colWidths=[4 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ])

    norms = {
        'Длина': (230, 260),
        'Ширина': (90, 105),
        'Обхват': (230, 250),
        'Индекс': (0.26, 0.29),
        'Угол пятки': (0, 4),
        'Угол пальца': (0, 8)
    }

    for row_idx in range(1, len(params_data)):
        param_text = params_data[row_idx][0]
        if isinstance(param_text, Paragraph):
            param_name = param_text.text
        else:
            param_name = str(param_text)

        for key, (low, high) in norms.items():
            if key in param_name:
                try:
                    left_val_text = params_data[row_idx][1]
                    if isinstance(left_val_text, Paragraph):
                        left_val_str = left_val_text.text
                    else:
                        left_val_str = str(left_val_text)

                    left_match = re.search(r'\d+\.?\d*', left_val_str)
                    if left_match:
                        left_val = float(left_match.group())
                        if left_val < low or left_val > high:
                            table_style.add('BACKGROUND', (1, row_idx), (1, row_idx), colors.HexColor('#FFF3CD'))

                    right_val_text = params_data[row_idx][2]
                    if isinstance(right_val_text, Paragraph):
                        right_val_str = right_val_text.text
                    else:
                        right_val_str = str(right_val_text)

                    right_match = re.search(r'\d+\.?\d*', right_val_str)
                    if right_match:
                        right_val = float(right_match.group())
                        if right_val < low or right_val > high:
                            table_style.add('BACKGROUND', (2, row_idx), (2, row_idx), colors.HexColor('#FFF3CD'))
                except (ValueError, AttributeError):
                    pass

    params_table.setStyle(table_style)
    story.append(params_table)
    story.append(Spacer(1, 0.8 * cm))

    length_diff = abs(data['foot_length']['left'] - data['foot_length']['right'])
    width_diff = abs(data['foot_width']['left'] - data['foot_width']['right'])

    asymmetry_text = f"""
    <font name='{normal_font}'><b>Анализ асимметрии:</b></font><br/>
    <font name='{normal_font}'>• Разница в длине: {length_diff:.1f} мм ({'норма' if length_diff <= 3 else 'требует внимания'})</font><br/>
    <font name='{normal_font}'>• Разница в ширине: {width_diff:.1f} мм ({'норма' if width_diff <= 2 else 'требует внимания'})</font><br/>
    <font name='{normal_font}'>• Тип стопы: {data['toe_type']}</font><br/>
    <font name='{normal_font}'>• Рекомендуемая ширина обуви: {data['shoe_width']}</font>
    """

    story.append(Paragraph(asymmetry_text, styles['BoxedText']))
    story.append(Spacer(1, 0.8 * cm))

    # ==================== РЕКОМЕНДАЦИИ ====================
    story.append(Paragraph("3. ПЕРСОНАЛИЗИРОВАННЫЕ РЕКОМЕНДАЦИИ", styles['SectionTitle']))
    story.append(Spacer(1, 0.4 * cm))

    intro_rec_text = f"""
    <font name='{normal_font}'>На основе анализа ваших данных сформированы следующие рекомендации:</font>
    """
    story.append(Paragraph(intro_rec_text, styles['Normal']))
    story.append(Spacer(1, 0.5 * cm))

    for i, rec in enumerate(recommendations):
        if rec['priority'] == 'high':
            title_color = HIGH_RISK_HEX
            priority_text = "Высокий приоритет"
        elif rec['priority'] == 'medium':
            title_color = MED_RISK_HEX
            priority_text = "Средний приоритет"
        else:
            title_color = LOW_RISK_HEX
            priority_text = "Общие рекомендации"

        story.append(Paragraph(
            f"<font name='{bold_font}' color='{title_color}'><b>{rec['title']}</b></font> "
            f"<font name='{normal_font}' size='8' color='{TEXT_MUTED_HEX}'>[{priority_text}]</font>",
            ParagraphStyle(name='RecTitle', parent=styles['Normal'],
                           fontSize=11, spaceBefore=10 if i > 0 else 0,
                           spaceAfter=4, alignment=TA_LEFT)
        ))

        story.append(Paragraph(
            f"<font name='{normal_font}'>{rec['description']}</font>",
            ParagraphStyle(name='RecDesc', parent=styles['Normal'],
                           fontSize=10, alignment=TA_LEFT,
                           leftIndent=10)
        ))

        if i < len(recommendations) - 1:
            story.append(Spacer(1, 0.3 * cm))

    story.append(Spacer(1, 1.2 * cm))

    conclusion_text = f"""
    <font name='{normal_font}'><b>Важно:</b> Данные рекомендации составлены на основе анализа от {data['scan_date']}. 
    При появлении болей, дискомфорта или изменений в походке обязательно обратитесь к врачу-ортопеду.</font>
    """

    story.append(Paragraph(conclusion_text, styles['BoxedText']))

    story.append(Spacer(1, 1.2 * cm))

    # ==================== ПОДВАЛ ====================
    story.append(Paragraph("_" * 70,
                           ParagraphStyle(name='FooterLine', parent=styles['Normal'],
                                          alignment=TA_CENTER, spaceBefore=10)))

    story.append(Spacer(1, 0.5 * cm))

    footer_text = f"""
    <font name='{normal_font}'><b>FootScan Analytics</b><br/>
    Цифровая лаборатория здоровья стоп</font><br/>
    <font name='{normal_font}' size='8'>Отчет сгенерирован автоматически {datetime.now().strftime('%d.%m.%Y %H:%M')}. 
    Данный документ носит рекомендательный характер и не заменяет консультацию специалиста.<br/>
    ID сканера: {data['scanner_id']} | Пациент: {data['client_name']}<br/>
    © 2024 FootScan Analytics. Все права защищены.</font>
    """

    story.append(Paragraph(footer_text,
                           ParagraphStyle(name='Footer', parent=styles['Normal'],
                                          alignment=TA_CENTER, fontSize=9,
                                          textColor=TEXT_MUTED)))

    # ==================== СОЗДАНИЕ PDF ====================
    print("[6/6] Генерация PDF файла...")
    try:
        doc.build(story)
        print(f"[SUCCESS] PDF отчет успешно создан: {output_filename}")

        debug_dir = "generated_reports_debug"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)

        safe_name = re.sub(r'[^\w\s-]', '', data['client_name'])
        safe_name = re.sub(r'[-\s]+', '_', safe_name).strip('-_')
        json_path = os.path.join(debug_dir, f"{safe_name}_{timestamp}_data.json")

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'data': data,
                'risk_scores': risk_scores,
                'recommendations': recommendations,
                'generated': datetime.now().isoformat(),
                'pdf_file': output_filename
            }, f, ensure_ascii=False, indent=2)

        print(f"[DEBUG] Данные отчета сохранены в: {json_path}")

    except Exception as e:
        print(f"[ERROR] Ошибка создания PDF: {e}")
        import traceback
        traceback.print_exc()

    return output_filename


# ============================================================================
# 8. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("🏥 FOOTSCAN ANALYTICS - Генератор медицинских отчетов")
    print("=" * 70)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(current_dir, "../reports")
    students_dir = os.path.join(reports_dir, "students")
    students_result_dir = os.path.join(reports_dir, "students_result")

    print(f"[INFO] Текущая директория: {current_dir}")
    print(f"[INFO] Директория с PDF файлами: {students_dir}")
    print(f"[INFO] Директория для результатов: {students_result_dir}")

    for directory in [students_dir, students_result_dir]:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"[INFO] Создана директория: {directory}")
            except Exception as e:
                print(f"[ERROR] Не удалось создать директорию {directory}: {e}")

    debug_dirs = ["extracted_data_debug", "generated_reports_debug", "temp_graphs"]
    for dir_name in debug_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

    pdf_patterns = [
        os.path.join(students_dir, "*.pdf"),
        os.path.join(students_dir, "*_Report.pdf"),
        os.path.join(current_dir, "*.pdf"),
        os.path.join(reports_dir, "*.pdf")
    ]

    pdf_files = []
    for pattern in pdf_patterns:
        found_files = glob.glob(pattern)
        for file in found_files:
            if file not in pdf_files and os.path.getsize(file) > 1000:
                pdf_files.append(file)

    pdf_files.sort()

    print(f"\n📁 НАЙДЕНО PDF ФАЙЛОВ: {len(pdf_files)}")
    if pdf_files:
        for i, pdf_file in enumerate(pdf_files, 1):
            size_kb = os.path.getsize(pdf_file) / 1024
            print(f"  {i:2d}. {os.path.basename(pdf_file)} ({size_kb:.1f} KB)")
    else:
        print("\n[ERROR] Не найдено ни одного PDF файла!")
        print("[INFO] Поместите PDF файлы в папку:")
        print(f"  • {students_dir}")

        manual_path = input("\nВведите путь к PDF файлу (или нажмите Enter для выхода): ").strip()
        if manual_path and os.path.exists(manual_path):
            pdf_files = [manual_path]
        else:
            print("[INFO] Выход из программы")
            return

    processed_count = 0
    failed_count = 0
    results = []

    print(f"\n{'=' * 70}")
    print("🚀 НАЧАЛО ОБРАБОТКИ ФАЙЛОВ")
    print('=' * 70)

    for pdf_index, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'=' * 60}")
        print(f"🔄 ОБРАБОТКА ФАЙЛА {pdf_index}/{len(pdf_files)}")
        print(f"📄 Файл: {os.path.basename(pdf_file)}")
        print(f"📏 Размер: {os.path.getsize(pdf_file) / 1024:.1f} KB")
        print('=' * 60)

        try:
            # Извлечение данных ИСКЛЮЧИТЕЛЬНО из PDF
            data = extract_data_from_pdf(pdf_file)

            # Проверка минимальных данных
            if data['foot_length']['left'] == 0:
                print(f"\n[ERROR] Не удалось извлечь данные из PDF!")
                print("[INFO] Проблема с чтением PDF файла")
                failed_count += 1
                continue

            # Расчет рисков
            risk_scores, recommendations = calculate_risk_scores(data)

            # Создание имени выходного файла
            safe_name = re.sub(r'[^\w\s-]', '', data['client_name'])
            safe_name = re.sub(r'[-\s]+', '_', safe_name).strip('-_')

            if not safe_name:
                safe_name = f"patient_{pdf_index}"

            output_filename = os.path.join(
                students_result_dir,
                f"FootScan_Report_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            # Генерация PDF отчета
            report_path = create_pdf_report(data, risk_scores, recommendations, output_filename)

            # Сохранение метаданных
            result_data = {
                'input_pdf': os.path.basename(pdf_file),
                'output_pdf': os.path.basename(report_path),
                'client_name': data['client_name'],
                'scan_date': data['scan_date'],
                'foot_length_left': data['foot_length']['left'],
                'foot_length_right': data['foot_length']['right'],
                'total_risk': sum(risk_scores.values()) / len(risk_scores),
                'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'file_size': os.path.getsize(report_path) if os.path.exists(report_path) else 0
            }

            results.append(result_data)
            processed_count += 1

            print(f"\n✅ УСПЕШНО ОБРАБОТАНО: {data['client_name']}")
            print(f"📊 Результат сохранен в: {report_path}")

        except Exception as e:
            print(f"\n❌ ОШИБКА ПРИ ОБРАБОТКЕ {pdf_file}: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1

    # ==================== ИТОГИ ====================
    print(f"\n{'=' * 70}")
    print("📈 ИТОГИ ОБРАБОТКИ")
    print('=' * 70)

    print(f"✅ Успешно обработано: {processed_count} файлов")
    print(f"❌ Не удалось обработать: {failed_count} файлов")
    print(f"📂 Всего найдено: {len(pdf_files)} файлов")

    if results:
        summary_file = os.path.join(students_result_dir,
                                    f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("FootScan Analytics - Итоги обработки\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Дата обработки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write(f"Успешно обработано: {processed_count} файлов\n")
            f.write(f"Не удалось обработать: {failed_count} файлов\n")
            f.write(f"Всего файлов: {len(pdf_files)}\n\n")

            f.write("=" * 70 + "\n")
            f.write("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:\n")
            f.write("=" * 70 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"{i:2d}. {result['client_name']}\n")
                f.write(f"    Входной файл: {result['input_pdf']}\n")
                f.write(f"    Выходной файл: {result['output_pdf']}\n")
                f.write(
                    f"    Длина стопы: Л={result['foot_length_left']:.1f}мм, П={result['foot_length_right']:.1f}мм\n")
                f.write(f"    Общий риск: {result['total_risk']:.1f}/100\n")
                f.write(f"    Дата сканирования: {result['scan_date']}\n")
                f.write(f"    Размер файла: {result['file_size']:,} байт\n")
                f.write("-" * 50 + "\n")

        print(f"\n📋 Итоговый отчет сохранен в: {summary_file}")

    print(f"\n📁 РЕЗУЛЬТАТЫ СОХРАНЕНЫ В:")
    print(f"   Отчеты PDF: {os.path.abspath(students_result_dir)}")
    print(f"   Извлеченные данные: {os.path.abspath('extracted_data_debug')}")
    print(f"   Данные отчетов: {os.path.abspath('generated_reports_debug')}")
    print(f"   Графики: {os.path.abspath('temp_graphs')}")

    if os.path.exists(students_result_dir):
        result_files = glob.glob(os.path.join(students_result_dir, "FootScan_Report_*.pdf"))
        if result_files:
            print(f"\n📄 СОЗДАННЫЕ ОТЧЕТЫ (первые 10):")
            for i, file in enumerate(sorted(result_files)[:10], 1):
                file_size = os.path.getsize(file) / 1024
                print(f"  {i:2d}. {os.path.basename(file)} ({file_size:.1f} KB)")

            if len(result_files) > 10:
                print(f"  ... и еще {len(result_files) - 10} файлов")

    print(f"\n{'=' * 70}")
    print("🎉 ОБРАБОТКА ЗАВЕРШЕНА!")
    print('=' * 70)

    if sys.platform == "win32":
        try:
            os.startfile(os.path.abspath(students_result_dir))
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            subprocess.call(["open", os.path.abspath(students_result_dir)])
        except Exception:
            pass


# ============================================================================
# 9. ЗАПУСК ПРОГРАММЫ
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='FootScan Analytics - Генератор медицинских отчетов')
    parser.add_argument('--clean', action='store_true', help='Очистка временных файлов перед запуском')
    parser.add_argument('--pdf', type=str, help='Путь к конкретному PDF файлу для обработки')

    args = parser.parse_args()

    if args.clean:
        print("[INFO] Очистка временных файлов...")
        for dir_name in ["temp_graphs", "extracted_data_debug", "generated_reports_debug"]:
            if os.path.exists(dir_name):
                import shutil

                try:
                    shutil.rmtree(dir_name)
                    print(f"[INFO] Удалена папка: {dir_name}")
                except Exception as e:
                    print(f"[WARNING] Не удалось удалить {dir_name}: {e}")

    if args.pdf:
        if os.path.exists(args.pdf):
            print(f"Обработка указанного файла: {args.pdf}")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            students_result_dir = os.path.join(current_dir, "students_result")

            if not os.path.exists(students_result_dir):
                os.makedirs(students_result_dir, exist_ok=True)

            data = extract_data_from_pdf(args.pdf)

            if data['foot_length']['left'] == 0:
                print("[ERROR] Не удалось извлечь данные из PDF!")
                print("[INFO] Проверьте структуру PDF файла")
                sys.exit(1)

            risk_scores, recommendations = calculate_risk_scores(data)

            safe_name = re.sub(r'[^\w\s-]', '', data['client_name'])
            safe_name = re.sub(r'[-\s]+', '_', safe_name).strip('-_')

            if not safe_name:
                safe_name = "patient"

            output_filename = os.path.join(
                students_result_dir,
                f"FootScan_Report_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            create_pdf_report(data, risk_scores, recommendations, output_filename)

            print(f"\n✅ Отчет создан: {output_filename}")
            print(f"📂 Папка с результатами: {os.path.abspath(students_result_dir)}")
        else:
            print(f"[ERROR] Файл не найден: {args.pdf}")
    else:
        main()

    print("\n👋 Программа завершена.")