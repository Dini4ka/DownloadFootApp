import re
import PyPDF2
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether
)
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.utils import simpleSplit
import matplotlib.pyplot as plt
import os
from PIL import Image as PILImage, ImageDraw, ImageFont
import matplotlib

matplotlib.use('Agg')  # Безголовый режим для сервера

# ============================================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# ============================================================================
# Цветовая палитра (современная, медицинская тематика)
PRIMARY_COLOR = colors.HexColor('#2E86AB')  # Основной синий
PRIMARY_DARK = colors.HexColor('#1B5E6E')  # Темный синий
SECONDARY_COLOR = colors.HexColor('#F18F01')  # Оранжевый акцент
LIGHT_BLUE = colors.HexColor('#E8F4F8')  # Светло-голубой фон
SUCCESS_COLOR = colors.HexColor('#4CAF50')  # Зеленый
WARNING_COLOR = colors.HexColor('#FF9800')  # Оранжевый
DANGER_COLOR = colors.HexColor('#F44336')  # Красный
NEUTRAL_COLOR = colors.HexColor('#9E9E9E')  # Серый

# Цвета для текста и границ
TEXT_MAIN = colors.HexColor('#1F2933')  # Основной текст
TEXT_MUTED = colors.HexColor('#7B8794')  # Второстепенный текст
BORDER_COLOR = colors.HexColor('#D3E2EA')  # Цвет границ

# Цвета для графиков Matplotlib
MATPLOT_PRIMARY = '#2E86AB'
MATPLOT_SECONDARY = '#F18F01'
MATPLOT_ACCENT = '#A5D8FF'
MATPLOT_LIGHT = '#E8F4F8'

# Хэши цветов для использования в HTML
SUCCESS_COLOR_HEX = '#4CAF50'
WARNING_COLOR_HEX = '#FF9800'
DANGER_COLOR_HEX = '#F44336'
PRIMARY_COLOR_HEX = '#2E86AB'
PRIMARY_DARK_HEX = '#1B5E6E'

# Настройки кодировки
import sys
import locale

# Устанавливаем UTF-8 везде
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
sys.stderr.reconfigure(encoding='utf-8') if hasattr(sys.stderr, 'reconfigure') else None

# Пробуем установить локаль
try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except locale.Error:
        pass


# ============================================================================
# 1. РЕГИСТРАЦИЯ ШРИФТОВ (ПРИОРИТЕТ: DejaVu -> Arial -> Резервные)
# ============================================================================
def register_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    font_normal = 'Helvetica'
    font_bold = 'Helvetica-Bold'

    # Список путей для поиска шрифтов DejaVu (распространенные расположения)
    dejavu_paths = [
        "dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf",
        "fonts/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/local/share/fonts/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/dejavusans.ttf",
    ]

    found_fonts = {'normal': None, 'bold': None}

    # Ищем DejaVu Sans
    for path in dejavu_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', path))
                found_fonts['normal'] = 'DejaVuSans'
                print(f"[SUCCESS] Зарегистрирован DejaVuSans: {path}")

                # Ищем жирную версию
                bold_path = path.replace('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf')
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_path))
                    found_fonts['bold'] = 'DejaVuSans-Bold'
                    print(f"[SUCCESS] Зарегистрирован DejaVuSans-Bold: {bold_path}")
                else:
                    # Используем обычный как жирный, если не нашли
                    found_fonts['bold'] = 'DejaVuSans'
                    print("[INFO] Жирный DejaVu не найден, используем обычный")

                return found_fonts['normal'], found_fonts['bold']

            except Exception as e:
                print(f"[WARNING] Ошибка регистрации DejaVu: {e}")

    # Если DejaVu не найден, пробуем Arial
    try:
        # Windows пути
        arial_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/ariali.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/arial.ttf",
        ]

        for path in arial_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('Arial', path))
                print(f"[SUCCESS] Зарегистрирован Arial: {path}")

                bold_path = path.replace('arial.ttf', 'arialbd.ttf')
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont('Arial-Bold', bold_path))
                    return 'Arial', 'Arial-Bold'
                else:
                    return 'Arial', 'Arial'

    except Exception as e:
        print(f"[WARNING] Ошибка регистрации Arial: {e}")

    # Резервные шрифты (стандартные PDF)
    print("[INFO] Используются стандартные шрифты PDF")
    return 'Helvetica', 'Helvetica-Bold'


# ============================================================================
# 2. ОБРАБОТКА ТЕКСТА И КОДИРОВОК
# ============================================================================
def clean_text(text):
    """Очищает текст от проблем с кодировкой и специальными символами"""
    if text is None:
        return ""

    # Если текст в bytes, декодируем
    if isinstance(text, bytes):
        encodings = ['utf-8', 'cp1251', 'cp866', 'iso-8859-1', 'koi8-r', 'mac_cyrillic']
        for encoding in encodings:
            try:
                text = text.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            # Если ничего не подошло, используем utf-8 с заменой ошибок
            text = text.decode('utf-8', errors='replace')

    # Удаляем непечатаемые символы
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Заменяем распространенные проблемы с кириллицей
    replacements = {
        # UTF-8 артефакты
        'â': '-', 'â': '—', 'â': "'", 'â': "'",
        'â': '"', 'â': '"', 'â¢': '•', 'â¦': '...',
        'â¡': '§', 'Â°': '°', 'Ã': 'А', 'Ð': 'Д',

        # Частые проблемы Windows-1251
        'ïðèìåð': 'пример',
        'ñòðàíèöû': 'страницы',
        'äîêóìåíò': 'документ',

        # Квадраты и прочее
        '□': '', '■': '', '▢': '', '�': '',

        # Множественные пробелы
        '  ': ' ', '   ': ' ', '\t': ' ', '\n\n\n': '\n\n'
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    # Восстанавливаем очевидные кириллические слова
    cyrillic_patterns = {
        r'Дл[иі]на': 'Длина',
        r'Ш[иі]р[иі]на': 'Ширина',
        r'[Иі]ндекс': 'Индекс',
        r'[Уу]гол': 'Угол',
        r'[Сс]топ[ыа]': 'стопы',
        r'[Пп]ятк[иа]': 'пятки',
        r'[Пп]альц[аы]': 'пальца',
    }

    for pattern, replacement in cyrillic_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text.strip()


# ============================================================================
# 3. СОЗДАНИЕ ЛОГОТИПА
# ============================================================================
def create_logo():
    """Создает простой логотип без ошибок"""
    logo_path = "logo_footscan.png"

    if not os.path.exists(logo_path):
        print("[INFO] Создание логотипа...")
        try:
            # Создаем простое изображение
            size = 200
            img = PILImage.new('RGB', (size, size), color='white')
            draw = ImageDraw.Draw(img)

            # Простой круг
            draw.ellipse([20, 20, size - 20, size - 20], outline='#2E86AB', width=3)

            # Простой текст
            try:
                font = ImageFont.truetype("dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Bold.ttf", 40)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", 40)
                except:
                    font = ImageFont.load_default()

            # Текст по центру
            text = "FSA"
            # Получаем размеры текста
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (size - text_width) // 2
                y = (size - text_height) // 2
                draw.text((x, y), text, fill='#2E86AB', font=font)
            except:
                # Простой текст по центру
                draw.text((size // 2 - 30, size // 2 - 20), text, fill='#2E86AB')

            img.save(logo_path, 'PNG')
            print(f"[SUCCESS] Простой логотип создан: {logo_path}")

        except Exception as e:
            print(f"[ERROR] Ошибка создания логотипа: {e}. Используем заглушку.")
            # Создаем простейший логотип
            img = PILImage.new('RGB', (100, 100), color=(46, 134, 171))
            draw = ImageDraw.Draw(img)
            draw.text((25, 40), "FSA", fill='white')
            img.save(logo_path, 'PNG')

    return logo_path


# ============================================================================
# 4. ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ PDF
# ============================================================================
def extract_data_from_pdf(pdf_path):
    """Извлекает данные из PDF с улучшенной обработкой кириллицы"""
    print(f"\n{'=' * 60}")
    print(f"📄 ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ: {pdf_path}")
    print('=' * 60)

    # Данные по умолчанию
    data = {
        'client_name': 'Иванов Иван Иванович',
        'foot_length': {'left': 274.7, 'right': 280.5},
        'foot_width': {'left': 112.5, 'right': 112.6},
        'arch_index': {'left': 0.24, 'right': 0.28},
        'heel_angle': {'left': 9, 'right': 4},
        'hallux_angle': {'left': 4.9, 'right': 8.1},
        'shoe_width': '> G',
        'shoe_size': {'left': 43.5, 'right': 44.5},
        'ball_girth': {'left': 270.5, 'right': 269.1},
        'toe_type': 'Египетский',
        'gender': 'Мужской',
        'scan_date': datetime.now().strftime('%d.%m.%Y'),
        'scanner_id': 'FS-001',
        'notes': ''
    }

    if pdf_path and os.path.exists(pdf_path):
        try:
            all_text = ""

            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)

                print(f"[INFO] PDF содержит {len(reader.pages)} страниц")

                for page_num, page in enumerate(reader.pages, 1):
                    # Извлекаем текст
                    text = page.extract_text()

                    if text:
                        cleaned_text = clean_text(text)
                        all_text += f"\n--- Страница {page_num} ---\n{cleaned_text}\n"

                    # Также пробуем извлечь текст с помощью других методов
                    if '/Annots' in page:
                        try:
                            for annot in page['/Annots']:
                                annot_obj = annot.get_object()
                                if '/Contents' in annot_obj:
                                    annot_text = annot_obj['/Contents']
                                    if annot_text:
                                        all_text += f"\n[Аннотация]: {clean_text(annot_text)}\n"
                        except Exception:
                            pass

            # Сохраняем сырой текст для отладки
            debug_path = "debug_extracted_text.txt"
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(all_text)
            print(f"[DEBUG] Сырой текст сохранен в: {debug_path}")

            # Парсим данные
            lines = all_text.split('\n')

            # Ищем имя
            name_patterns = [
                r'(?:Пациент|Клиент|ФИО|Имя)[:\s]+([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
                r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)'
            ]

            for line in lines:
                for pattern in name_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        data['client_name'] = match.group(1).strip()
                        print(f"[FOUND] Имя: {data['client_name']}")
                        break
                if data['client_name'] != 'Иванов Иван Иванович':
                    break

            # Ищем числовые данные
            for line in lines:
                line_lower = line.lower()

                # Длина стопы
                if any(word in line_lower for word in ['длина', 'length', 'l=', 'дл.']):
                    numbers = re.findall(r'\d+[.,]?\d*', line)
                    if len(numbers) >= 2:
                        try:
                            left_val = float(numbers[0].replace(',', '.'))
                            right_val = float(numbers[1].replace(',', '.'))
                            if 200 <= left_val <= 350 and 200 <= right_val <= 350:
                                data['foot_length'] = {'left': left_val, 'right': right_val}
                                print(f"[FOUND] Длина стопы: Л={left_val}, П={right_val}")
                        except ValueError:
                            pass

                # Ширина стопы
                elif any(word in line_lower for word in ['ширина', 'width', 'w=', 'шир.']):
                    numbers = re.findall(r'\d+[.,]?\d*', line)
                    if len(numbers) >= 2:
                        try:
                            left_val = float(numbers[0].replace(',', '.'))
                            right_val = float(numbers[1].replace(',', '.'))
                            if 80 <= left_val <= 150 and 80 <= right_val <= 150:
                                data['foot_width'] = {'left': left_val, 'right': right_val}
                                print(f"[FOUND] Ширина стопы: Л={left_val}, П={right_val}")
                        except ValueError:
                            pass

                # Индекс свода
                elif any(word in line_lower for word in ['индекс', 'index', 'арч', 'arch']):
                    numbers = re.findall(r'0?\.\d+|\d+[.,]\d+', line)
                    if len(numbers) >= 2:
                        try:
                            left_val = float(numbers[0].replace(',', '.'))
                            right_val = float(numbers[1].replace(',', '.'))
                            if 0.1 <= left_val <= 0.4 and 0.1 <= right_val <= 0.4:
                                data['arch_index'] = {'left': left_val, 'right': right_val}
                                print(f"[FOUND] Индекс свода: Л={left_val}, П={right_val}")
                        except ValueError:
                            pass

                # Угол пятки
                elif any(word in line_lower for word in ['угол пятки', 'heel', 'пятка', 'варус']):
                    numbers = re.findall(r'-?\d+[.,]?\d*', line)
                    if len(numbers) >= 2:
                        try:
                            left_val = int(float(numbers[0].replace(',', '.')))
                            right_val = int(float(numbers[1].replace(',', '.')))
                            if -20 <= left_val <= 20 and -20 <= right_val <= 20:
                                data['heel_angle'] = {'left': left_val, 'right': right_val}
                                print(f"[FOUND] Угол пятки: Л={left_val}°, П={right_val}°")
                        except ValueError:
                            pass

            print(f"\n{'=' * 60}")
            print("📊 ИЗВЛЕЧЕННЫЕ ДАННЫЕ:")
            print('=' * 60)
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"{key}: {value}")
                else:
                    print(f"{key}: {value}")

        except Exception as e:
            print(f"[ERROR] Ошибка чтения PDF: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("[INFO] Файл PDF не найден, используются демо-данные")

    return data


# ============================================================================
# 5. РАСЧЕТ РИСКОВ
# ============================================================================
def calculate_risk_scores(data):
    """Рассчитывает риски на основе данных"""
    print(f"\n{'=' * 60}")
    print("⚖️ РАСЧЕТ РИСКОВ")
    print('=' * 60)

    scores = {
        'degenerative': 30,  # Дегенеративный (суставы)
        'spinal': 30,  # Позвоночный
        'traumatic': 30,  # Травматический
        'comfort': 30,  # Комфорт
        'progression': 30  # Прогрессия
    }

    # Анализ индекса свода
    avg_arch = (data['arch_index']['left'] + data['arch_index']['right']) / 2
    if avg_arch < 0.26:
        scores['degenerative'] += 20
        scores['spinal'] += 15
        print(f"  ⚠️ Высокий свод стопы: {avg_arch:.3f}")
    elif avg_arch > 0.29:
        scores['traumatic'] += 15
        print(f"  ⚠️ Низкий свод стопы: {avg_arch:.3f}")

    # Асимметрия длины
    length_diff = abs(data['foot_length']['left'] - data['foot_length']['right'])
    if length_diff > 5:
        scores['spinal'] += 15
        scores['progression'] += 10
        print(f"  ⚠️ Асимметрия длины: {length_diff:.1f} мм")

    # Асимметрия ширины
    width_diff = abs(data['foot_width']['left'] - data['foot_width']['right'])
    if width_diff > 3:
        scores['comfort'] += 10
        print(f"  ⚠️ Асимметрия ширины: {width_diff:.1f} мм")

    # Угол пятки
    for side in ['left', 'right']:
        angle = data['heel_angle'][side]
        if abs(angle) > 6:
            scores['traumatic'] += 10
            scores['comfort'] += 5
            side_name = 'Левой' if side == 'left' else 'Правой'
            print(f"  ⚠️ Отклонение {side_name} пятки: {angle}°")

    # Нормализация
    for key in scores:
        scores[key] = max(0, min(100, scores[key]))

    # Вывод результатов
    risk_levels = []
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

        risk_levels.append((name, score, level, emoji))
        print(f"  {emoji} {name}: {score}/100 ({level})")

    return scores


# ============================================================================
# 6. СОЗДАНИЕ ГРАФИКОВ
# ============================================================================
def create_radar_chart(risk_scores, output_path):
    """Создает радарную диаграмму рисков"""
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.unicode_minus': False,
        'figure.autolayout': True,
        'savefig.dpi': 150,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1
    })

    # Категории
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
    categories_radar = categories + [categories[0]]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))

    # Настройка
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories_radar[:-1], fontsize=9, color='#1F2933')

    # Оси Y
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0', '25', '50', '75', '100'], fontsize=8, color='#7B8794')
    ax.grid(True, alpha=0.3, color='#D3E2EA', linestyle='--', linewidth=0.5)

    # Цветовые зоны
    ax.fill_between(angles, 0, 40, color='#4CAF50', alpha=0.1)
    ax.fill_between(angles, 40, 70, color='#FF9800', alpha=0.1)
    ax.fill_between(angles, 70, 100, color='#F44336', alpha=0.1)

    # Линии зон
    ax.plot(angles, [40] * len(angles), color='#4CAF50', alpha=0.5, linewidth=0.5)
    ax.plot(angles, [70] * len(angles), color='#FF9800', alpha=0.5, linewidth=0.5)

    # Данные
    ax.plot(angles, values, 'o-', linewidth=2, color=MATPLOT_PRIMARY,
            markersize=6, markerfacecolor='white', markeredgewidth=1.5)
    ax.fill(angles, values, alpha=0.15, color=MATPLOT_PRIMARY)

    # Точки значений
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + 4, f'{value:.0f}',
                ha='center', va='center', fontsize=7, fontweight='bold')

    # Заголовок
    plt.title('Профиль биомеханических рисков', size=12, pad=20, fontweight='bold', color='#1B5E6E')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"[GRAPH] Радарная диаграмма сохранена: {output_path}")
    return output_path


def create_comparison_chart(data, output_path):
    """Создает сравнительную диаграмму параметров стоп"""
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.unicode_minus': False,
        'figure.autolayout': True
    })

    # Подготовка данных
    categories = ['Длина\nстопы, мм', 'Ширина\nстопы, мм',
                  'Индекс\nсвода (×100)', 'Угол\nпятки, °']

    left_values = [
        data['foot_length']['left'],
        data['foot_width']['left'],
        data['arch_index']['left'] * 100,
        data['heel_angle']['left']
    ]

    right_values = [
        data['foot_length']['right'],
        data['foot_width']['right'],
        data['arch_index']['right'] * 100,
        data['heel_angle']['right']
    ]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))

    # Столбцы
    bars_left = ax.bar(x - width / 2, left_values, width,
                       label='Левая стопа', color=MATPLOT_PRIMARY, alpha=0.85,
                       edgecolor='white', linewidth=1)

    bars_right = ax.bar(x + width / 2, right_values, width,
                        label='Правая стопа', color=MATPLOT_SECONDARY, alpha=0.85,
                        edgecolor='white', linewidth=1)

    # Настройки
    ax.set_ylabel('Значение', fontsize=10, fontweight='bold')
    ax.set_title('Сравнительный анализ стоп', fontsize=12, fontweight='bold',
                 pad=15, color='#1B5E6E')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9)
    ax.legend(loc='upper right', fontsize=9)

    # Сетка
    ax.grid(True, alpha=0.2, axis='y', linestyle='--')
    ax.set_axisbelow(True)

    # Значения на столбцах
    def autolabel(bars, color):
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height,
                    f'{height:.1f}', ha='center', va='bottom',
                    fontsize=8, fontweight='bold')

    autolabel(bars_left, MATPLOT_PRIMARY)
    autolabel(bars_right, MATPLOT_SECONDARY)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"[GRAPH] Сравнительная диаграмма сохранена: {output_path}")
    return output_path


# ============================================================================
# 7. ГЕНЕРАЦИЯ PDF ОТЧЕТА
# ============================================================================
def create_pdf_report(data, risk_scores, output_filename):
    """Создает профессиональный PDF отчет"""
    print(f"\n{'=' * 60}")
    print("📄 СОЗДАНИЕ PDF ОТЧЕТА")
    print('=' * 60)

    # Регистрируем шрифты
    normal_font, bold_font = register_fonts()
    print(f"[INFO] Используемые шрифты: {normal_font} / {bold_font}")

    # Создаем графики
    print("[1/5] Создание графиков...")
    radar_chart_path = "temp_radar_chart.png"
    comparison_chart_path = "temp_comparison_chart.png"

    create_radar_chart(risk_scores, radar_chart_path)
    create_comparison_chart(data, comparison_chart_path)

    # Создаем логотип
    logo_path = create_logo()

    # Настройка документа
    print("[2/5] Настройка документа...")
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
    styles = getSampleStyleSheet()

    # Настройка стилей
    # Базовый стиль
    styles['Normal'].fontName = normal_font
    styles['Normal'].fontSize = 10
    styles['Normal'].textColor = colors.black
    styles['Normal'].leading = 14
    styles['Normal'].alignment = TA_JUSTIFY

    # Заголовок компании
    styles.add(ParagraphStyle(
        name='CompanyTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=22,
        textColor=PRIMARY_DARK,
        alignment=TA_CENTER,
        spaceAfter=6
    ))

    # Подзаголовок
    styles.add(ParagraphStyle(
        name='CompanySubtitle',
        parent=styles['Normal'],
        fontName=normal_font,
        fontSize=11,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER,
        spaceAfter=20
    ))

    # Заголовок отчета
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=18,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=12
    ))

    # Заголовок раздела
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=14,
        textColor=PRIMARY_DARK,
        spaceBefore=18,
        spaceAfter=8,
        borderWidth=0,
        borderPadding=0,
        leftIndent=0
    ))

    # Подраздел
    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=12,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=6
    ))

    # Важный текст
    styles.add(ParagraphStyle(
        name='Important',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=10,
        textColor=colors.black,
        backColor=LIGHT_BLUE,
        borderPadding=5,
        spaceAfter=4
    ))

    # Мелкий текст
    styles.add(ParagraphStyle(
        name='Small',
        parent=styles['Normal'],
        fontSize=8,
        textColor=TEXT_MUTED,
        leading=10
    ))

    # Текст в рамке
    styles.add(ParagraphStyle(
        name='BoxedText',
        parent=styles['Normal'],
        fontSize=9,
        backColor=LIGHT_BLUE,
        borderColor=BORDER_COLOR,
        borderWidth=1,
        borderPadding=8,
        leading=12
    ))

    # ==================== ТИТУЛЬНАЯ СТРАНИЦА ====================
    print("[3/5] Формирование титульной страницы...")

    # Логотип
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=3.5 * cm, height=3.5 * cm)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.5 * cm))
        except Exception as e:
            print(f"[WARNING] Не удалось загрузить логотип: {e}")

    # Заголовки
    story.append(Paragraph("FootScan Analytics", styles['CompanyTitle']))
    story.append(Paragraph("Цифровая лаборатория здоровья стоп", styles['CompanySubtitle']))

    story.append(Spacer(1, 1.2 * cm))

    story.append(Paragraph("ПЕРСОНАЛИЗИРОВАННЫЙ ОТЧЕТ", styles['ReportTitle']))
    story.append(Paragraph("Анализ биомеханики стоп и рекомендации",
                           ParagraphStyle(name='ReportSubtitle', parent=styles['Normal'],
                                          alignment=TA_CENTER, spaceAfter=15)))

    story.append(Spacer(1, 1.5 * cm))

    # Информация о пациенте
    patient_info = [
        [Paragraph("<b>Пациент</b>", styles['Important']),
         Paragraph(data['client_name'], styles['Normal'])],
        [Paragraph("<b>Дата обследования</b>", styles['Important']),
         Paragraph(data.get('scan_date', datetime.now().strftime('%d.%m.%Y')), styles['Normal'])],
        [Paragraph("<b>ID отчета</b>", styles['Important']),
         Paragraph(f"FSA-{datetime.now().strftime('%Y%m%d%H%M')}", styles['Normal'])],
        [Paragraph("<b>Сканер</b>", styles['Important']),
         Paragraph(data.get('scanner_id', 'FS-001'), styles['Normal'])],
    ]

    patient_table = Table(patient_info, colWidths=[4 * cm, 9 * cm])
    patient_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE),
        ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 10),
        ('RIGHTPADDING', (1, 0), (1, -1), 10),
    ]))

    story.append(patient_table)
    story.append(Spacer(1, 1.8 * cm))

    # Введение
    intro_text = """
    <b>Данный отчет содержит:</b><br/>
    • Анализ биомеханических параметров ваших стоп<br/>
    • Оценку индивидуальных рисков для здоровья<br/>
    • Персонализированные рекомендации по подбору обуви<br/>
    • Советы по поддержанию здоровья стоп<br/>
    """

    story.append(Paragraph(intro_text, styles['BoxedText']))

    story.append(Spacer(1, 2 * cm))

    # Конфиденциальность
    story.append(Paragraph(
        "КОНФИДЕНЦИАЛЬНЫЙ МЕДИЦИНСКИЙ ДОКУМЕНТ<br/>"
        "Предназначен только для пациента и лечащего врача",
        ParagraphStyle(
            name='Confidential',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=9,
            textColor=NEUTRAL_COLOR,
            alignment=TA_CENTER,
            spaceAfter=0
        )
    ))

    story.append(PageBreak())

    # ==================== СТРАНИЦА 2: АНАЛИЗ РИСКОВ ====================
    print("[4/5] Формирование страницы анализа рисков...")

    story.append(Paragraph("1. АНАЛИЗ БИОМЕХАНИЧЕСКИХ РИСКОВ", styles['SectionTitle']))
    story.append(Spacer(1, 0.4 * cm))

    # Текст анализа (используем hex-значения напрямую)
    analysis_text = f"""
    На основе анализа параметров ваших стоп, система определила индивидуальный профиль рисков. 
    Уровень риска оценивается по шкале от 0 до 100 баллов, где:<br/>
    • <font color="{SUCCESS_COLOR_HEX}"><b>0-49</b></font> — низкий риск<br/>
    • <font color="{WARNING_COLOR_HEX}"><b>50-69</b></font> — умеренный риск<br/>
    • <font color="{DANGER_COLOR_HEX}"><b>70-100</b></font> — высокий риск<br/>
    <br/>
    Рекомендуется обратить особое внимание на категории с оценкой выше 50 баллов.
    """

    story.append(Paragraph(analysis_text, styles['Normal']))
    story.append(Spacer(1, 0.8 * cm))

    # Радарная диаграмма
    if os.path.exists(radar_chart_path):
        try:
            radar_img = Image(radar_chart_path, width=14 * cm, height=14 * cm)
            radar_img.hAlign = 'CENTER'
            story.append(radar_img)
            story.append(Spacer(1, 0.5 * cm))
        except Exception as e:
            print(f"[WARNING] Не удалось загрузить радарную диаграмму: {e}")
            story.append(Paragraph("[Диаграмма рисков не загружена]", styles['Normal']))

    # Таблица рисков
    risk_data = []
    risk_categories = [
        ('Дегенеративный риск', 'Риск развития артрозов и дегенеративных изменений суставов',
         risk_scores['degenerative']),
        ('Позвоночный риск', 'Влияние на осанку и здоровье позвоночника',
         risk_scores['spinal']),
        ('Травматический риск', 'Вероятность получения травм при нагрузках',
         risk_scores['traumatic']),
        ('Комфортный риск', 'Сложности с подбором комфортной обуви',
         risk_scores['comfort']),
        ('Риск прогрессирования', 'Вероятность усугубления существующих особенностей',
         risk_scores['progression'])
    ]

    for name, description, score in risk_categories:
        if score >= 70:
            color = DANGER_COLOR
            level = "ВЫСОКИЙ"
        elif score >= 50:
            color = WARNING_COLOR
            level = "УМЕРЕННЫЙ"
        else:
            color = SUCCESS_COLOR
            level = "НИЗКИЙ"

        risk_data.append([
            Paragraph(f"<b>{name}</b><br/><font size=7>{description}</font>",
                      ParagraphStyle(name='RiskDesc', parent=styles['Normal'], fontSize=9)),
            Paragraph(f"<b>{score}/100</b>",
                      ParagraphStyle(name='RiskScore', parent=styles['Normal'],
                                     fontSize=10, textColor=color, alignment=TA_CENTER)),
            Paragraph(level,
                      ParagraphStyle(name='RiskLevel', parent=styles['Normal'],
                                     fontName=bold_font, fontSize=9, textColor=color,
                                     alignment=TA_CENTER))
        ])

    risk_table = Table(risk_data, colWidths=[7 * cm, 3 * cm, 3.5 * cm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
    ]))

    story.append(risk_table)
    story.append(Spacer(1, 0.8 * cm))

    # Интерпретация
    interpretation = []
    for name, _, score in risk_categories:
        if score >= 70:
            interpretation.append(f"• <b>{name.split()[0]}</b> — требуется консультация специалиста")
        elif score >= 50:
            interpretation.append(f"• <b>{name.split()[0]}</b> — рекомендуется наблюдение")

    if interpretation:
        story.append(Paragraph("<b>Ключевые выводы:</b>", styles['SubSection']))
        for item in interpretation:
            story.append(Paragraph(item, styles['Normal']))

    story.append(PageBreak())

    # ==================== СТРАНИЦА 3: ДЕТАЛЬНЫЙ АНАЛИЗ ====================
    print("[5/5] Формирование страницы детального анализа...")

    story.append(Paragraph("2. ДЕТАЛЬНЫЙ БИОМЕХАНИЧЕСКИЙ АНАЛИЗ", styles['SectionTitle']))
    story.append(Spacer(1, 0.4 * cm))

    # Сравнительная диаграмма
    if os.path.exists(comparison_chart_path):
        try:
            comp_img = Image(comparison_chart_path, width=15 * cm, height=9 * cm)
            comp_img.hAlign = 'CENTER'
            story.append(comp_img)
            story.append(Spacer(1, 0.5 * cm))
        except Exception as e:
            print(f"[WARNING] Не удалось загрузить сравнительную диаграмму: {e}")

    # Таблица параметров
    story.append(Paragraph("Измеренные параметры стоп:", styles['SubSection']))

    params_data = [
        [Paragraph("<b>Параметр</b>", styles['Important']),
         Paragraph("<b>Левая стопа</b>", styles['Important']),
         Paragraph("<b>Правая стопа</b>", styles['Important']),
         Paragraph("<b>Нормальный диапазон</b>", styles['Important'])],

        ['Длина стопы (мм)',
         f"{data['foot_length']['left']:.1f}",
         f"{data['foot_length']['right']:.1f}",
         '240–280 мм'],

        ['Ширина стопы (мм)',
         f"{data['foot_width']['left']:.1f}",
         f"{data['foot_width']['right']:.1f}",
         '90–110 мм'],

        ['Индекс свода',
         f"{data['arch_index']['left']:.3f}",
         f"{data['arch_index']['right']:.3f}",
         '0.26–0.29'],

        ['Угол пятки (°)',
         f"{data['heel_angle']['left']}",
         f"{data['heel_angle']['right']}",
         '0–6°'],

        ['Угол большого пальца (°)',
         f"{data['hallux_angle']['left']:.1f}",
         f"{data['hallux_angle']['right']:.1f}",
         '0–10°'],
    ]

    params_table = Table(params_data, colWidths=[4 * cm, 2.8 * cm, 2.8 * cm, 4 * cm])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
    ])

    # Подсветка отклонений от нормы
    norms = {
        'Длина': (240, 280),
        'Ширина': (90, 110),
        'Индекс': (0.26, 0.29),
        'Угол пятки': (0, 6),
        'Угол большого пальца': (0, 10)
    }

    for row_idx in range(1, len(params_data)):
        param_name = params_data[row_idx][0]
        for key, (low, high) in norms.items():
            if key in param_name:
                try:
                    # Левая стопа
                    left_val = float(params_data[row_idx][1])
                    if left_val < low or left_val > high:
                        table_style.add('BACKGROUND', (1, row_idx), (1, row_idx), colors.HexColor('#FFF3CD'))

                    # Правая стопа
                    right_val = float(params_data[row_idx][2])
                    if right_val < low or right_val > high:
                        table_style.add('BACKGROUND', (2, row_idx), (2, row_idx), colors.HexColor('#FFF3CD'))
                except ValueError:
                    pass

    params_table.setStyle(table_style)
    story.append(params_table)
    story.append(Spacer(1, 0.8 * cm))

    # Интерпретация параметров
    interpretation_text = """
    <b>Интерпретация параметров:</b><br/>
    • <b>Асимметрия более 5 мм</b> в длине или ширине может указывать на различия в биомеханике<br/>
    • <b>Индекс свода ниже 0.26</b> свидетельствует о высоком своде (полая стопа)<br/>
    • <b>Индекс свода выше 0.29</b> указывает на низкий свод (плоскостопие)<br/>
    • <b>Угол пятки более 6°</b> может говорить о варусной/вальгусной установке<br/>
    """

    story.append(Paragraph(interpretation_text, styles['BoxedText']))
    story.append(Spacer(1, 0.8 * cm))

    # ==================== РЕКОМЕНДАЦИИ ====================
    story.append(Paragraph("3. РЕКОМЕНДАЦИИ", styles['SectionTitle']))
    story.append(Spacer(1, 0.4 * cm))

    recommendations = [
        ("👟 Подбор обуви",
         "Рекомендуется обувь с расширенной колодкой (ширина G/H), "
         "поддержкой свода и стабилизацией пятки. Избегайте узких носов и высоких каблуков."),

        ("🩹 Ортопедические стельки",
         "Рассмотрите возможность изготовления индивидуальных стелек полного контакта "
         "с поддержкой продольного и поперечного сводов."),

        ("🏃 Физическая активность",
         "Упражнения для укрепления мышц стопы и голени. Ходьба босиком по неровным "
         "поверхностям (песок, трава). Избегайте резкого увеличения нагрузок."),

        ("⚕️ Наблюдение",
         "При наличии дискомфорта или болей рекомендуется консультация врача-ортопеда. "
         "Повторное обследование через 6-12 месяцев для контроля динамики."),

        ("🚶 Повседневные привычки",
         "Регулярные перерывы при длительном стоянии или ходьбе. Массаж стоп после нагрузок. "
         "Использование удобной обуви в повседневной жизни.")
    ]

    for i, (title, text) in enumerate(recommendations):
        story.append(Paragraph(f"<b>{title}</b>",
                               ParagraphStyle(name='RecTitle', parent=styles['Normal'],
                                              fontName=bold_font, fontSize=11,
                                              textColor=PRIMARY_COLOR,
                                              spaceBefore=8 if i > 0 else 0,
                                              spaceAfter=4)))
        story.append(Paragraph(text, styles['Normal']))
        if i < len(recommendations) - 1:
            story.append(Spacer(1, 0.3 * cm))

    story.append(Spacer(1, 1.2 * cm))

    # ==================== ПОДВАЛ ====================
    # Разделительная линия
    story.append(Paragraph("_" * 70,
                           ParagraphStyle(name='FooterLine', parent=styles['Normal'],
                                          alignment=TA_CENTER, spaceBefore=10)))

    story.append(Spacer(1, 0.5 * cm))

    # Информация о компании
    footer_text = """
    <b>FootScan Analytics</b><br/>
    Цифровая лаборатория здоровья стоп<br/>
    <font size=8>Отчет сгенерирован автоматически. 
    Данный документ носит рекомендательный характер и не заменяет консультацию специалиста.<br/>
    © 2024 FootScan Analytics. Все права защищены.</font>
    """

    story.append(Paragraph(footer_text,
                           ParagraphStyle(name='Footer', parent=styles['Normal'],
                                          alignment=TA_CENTER, fontSize=9,
                                          textColor=TEXT_MUTED)))

    # ==================== СОЗДАНИЕ PDF ====================
    print("[INFO] Генерация PDF файла...")
    try:
        doc.build(story)
        print(f"[SUCCESS] PDF отчет успешно создан: {output_filename}")
    except Exception as e:
        print(f"[ERROR] Ошибка создания PDF: {e}")
        import traceback
        traceback.print_exc()

    # Очистка временных файлов
    for temp_file in [radar_chart_path, comparison_chart_path]:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

    # Сохраняем данные для отладки
    import json
    with open("report_data_debug.json", "w", encoding='utf-8') as f:
        json.dump({
            'data': data,
            'risk_scores': risk_scores,
            'generated': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

    return output_filename


# ============================================================================
# 8. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================================
def main():
    print("\n" + "=" * 70)
    print("🏥 FOOTSCAN ANALYTICS - Генератор медицинских отчетов")
    print("=" * 70)

    # Поиск PDF файла
    pdf_files = [
        "Денис_Карелов_100904_000014_Report.pdf",
        "reports/Денис_Карелов_100904_000014/Денис_Карелов_100904_000014_Report.pdf",
        "Denis_Karelov_report.pdf",
        "report.pdf"
    ]

    pdf_path = None
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            pdf_path = pdf_file
            break

    if pdf_path:
        print(f"[INFO] Найден PDF файл: {pdf_path}")
        data = extract_data_from_pdf(pdf_path)
    else:
        print("[INFO] PDF файл не найден, используются демонстрационные данные")
        # Демо-данные
        data = {
            'client_name': 'Денис Карелов',
            'foot_length': {'left': 274.7, 'right': 280.5},
            'foot_width': {'left': 112.5, 'right': 112.6},
            'arch_index': {'left': 0.24, 'right': 0.28},
            'heel_angle': {'left': 9, 'right': 4},
            'hallux_angle': {'left': 4.9, 'right': 8.1},
            'shoe_width': '> G',
            'shoe_size': {'left': 43.5, 'right': 44.5},
            'ball_girth': {'left': 270.5, 'right': 269.1},
            'toe_type': 'Египетский',
            'gender': 'Мужской',
            'scan_date': '10.09.2024',
            'scanner_id': 'FS-001'
        }

    # Расчет рисков
    risk_scores = calculate_risk_scores(data)

    # Генерация отчета
    safe_name = data['client_name'].replace(' ', '_').replace('.', '')
    output_pdf = f"FootScan_Report_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

    create_pdf_report(data, risk_scores, output_pdf)

    print("\n" + "=" * 70)
    print("✅ ОТЧЕТ УСПЕШНО СОЗДАН!")
    print("=" * 70)
    print(f"📄 Файл отчета: {output_pdf}")
    print(f"👤 Пациент: {data['client_name']}")
    print(f"📅 Дата: {data.get('scan_date', datetime.now().strftime('%d.%m.%Y'))}")
    print(f"📊 Уровень риска: {max(risk_scores.values())}/100")

    # Дополнительная информация
    total_risk = sum(risk_scores.values()) / len(risk_scores)
    if total_risk >= 70:
        risk_level = "высокий"
    elif total_risk >= 50:
        risk_level = "умеренный"
    else:
        risk_level = "низкий"

    print(f"⚖️  Общий уровень: {risk_level} ({total_risk:.1f}/100)")
    print("=" * 70)

    # Открытие файла (если в Windows)
    if os.name == 'nt' and os.path.exists(output_pdf):
        try:
            os.startfile(output_pdf)
        except Exception:
            pass
    elif os.path.exists(output_pdf):
        print(f"[INFO] Отчет сохранен по пути: {os.path.abspath(output_pdf)}")


# ============================================================================
# ЗАПУСК
# ============================================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Программа прервана пользователем")
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        print("\n[INFO] Проверьте наличие необходимых библиотек:")
        print("pip install PyPDF2 reportlab matplotlib numpy pillow")