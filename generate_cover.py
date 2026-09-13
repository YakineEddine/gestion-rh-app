import os
from PIL import Image, ImageDraw, ImageFont

def create_esprit_cover(output_path):
    width, height = 2480, 3508
    im = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)

    font_dir = r"C:\Windows\Fonts"
    f_arial_b_huge = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 140)
    f_arial_b_title = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 82)
    f_arial_title = ImageFont.truetype(os.path.join(font_dir, "arial.ttf"), 78)
    f_arial_b_field = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 64)
    f_arial_field = ImageFont.truetype(os.path.join(font_dir, "arial.ttf"), 60)
    f_slogan = ImageFont.truetype(os.path.join(font_dir, "arial.ttf"), 52)
    f_year = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 58)

    # Fonts for the red triangle subject
    f_tri_badge = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 40)
    f_tri_main = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 32)
    f_tri_bold = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 36)
    f_tri_sub = ImageFont.truetype(os.path.join(font_dir, "arial.ttf"), 30)

    # Colors
    c_red = (196, 22, 28)        # ESPRIT Red
    c_dark_red = (160, 15, 20)   # Ribbon Red
    c_black = (26, 26, 26)       # Dark Black
    c_dark_grey = (70, 70, 72)
    c_med_grey = (150, 152, 154)
    c_light_grey = (220, 222, 224)
    c_bg_poly = (242, 244, 246)

    # 1. Top-left dark tab
    draw.rounded_rectangle([0, 0, 750, 420], radius=40, fill=c_black)

    # 2. Geometric triangles on the left side
    triangles = [
        ([(0, 420), (220, 480), (0, 700)], c_red, None, 0),
        ([(0, 700), (220, 480), (280, 780)], c_dark_grey, None, 0),
        ([(0, 700), (280, 780), (0, 950)], c_black, None, 0),
        ([(220, 480), (450, 520), (280, 780)], None, c_med_grey, 4),
        ([(280, 780), (450, 520), (550, 750)], c_bg_poly, c_light_grey, 3),
        ([(280, 780), (550, 750), (420, 960)], None, c_med_grey, 4),
        ([(0, 950), (280, 780), (420, 960)], c_med_grey, None, 0),
        ([(0, 950), (420, 960), (120, 1200)], c_dark_red, None, 0),
        ([(420, 960), (620, 1020), (480, 1240)], None, c_light_grey, 3),
        ([(120, 1200), (420, 960), (480, 1240)], c_light_grey, None, 0),
        ([(0, 950), (120, 1200), (0, 1400)], c_dark_grey, None, 0),
        
        # Across and below the red banner
        ([(0, 1400), (240, 1480), (0, 1620)], c_light_grey, None, 0),
        ([(240, 1480), (480, 1550), (320, 1620)], None, c_med_grey, 4),
        
        # Bottom left mosaic
        ([(0, 2650), (320, 2700), (0, 2880)], c_black, None, 0),
        ([(0, 2880), (320, 2700), (220, 2980)], c_dark_grey, None, 0),
        ([(220, 2980), (480, 2820), (550, 3080)], None, c_light_grey, 4),
        ([(0, 2880), (220, 2980), (0, 3180)], c_dark_grey, None, 0),
        ([(0, 3180), (220, 2980), (320, 3240)], c_red, None, 0),
        ([(320, 3240), (550, 3080), (600, 3360)], None, c_light_grey, 4),
        ([(0, 3180), (320, 3240), (0, 3508)], c_black, None, 0),
        ([(0, 3508), (320, 3240), (480, 3508)], c_red, None, 0),
    ]

    for pts, fill, outline, ow in triangles:
        draw.polygon(pts, fill=fill, outline=outline, width=ow)

    # Watermark triangles on the right side
    watermarks = [
        ([(1950, 1200), (2250, 1300), (2050, 1550)], None, (230, 210, 210), 5),
        ([(1700, 1350), (1950, 1420), (1800, 1680)], (250, 240, 240), None, 0),
        ([(1400, 2100), (2300, 2400), (1600, 3300)], (244, 246, 248), None, 0),
    ]
    for pts, fill, outline, ow in watermarks:
        draw.polygon(pts, fill=fill, outline=outline, width=ow)

    # 3. PROMINENT RED TRIANGLE CONTAINING THE SUBJECT
    # Top vertex at (0, 1580), Apex at (850, 2120), Bottom vertex at (0, 2660)
    tri_subject = [(0, 1580), (850, 2120), (0, 2660)]
    tri_shadow = [(6, 1586), (860, 2126), (6, 2670)]
    draw.polygon(tri_shadow, fill=(215, 218, 222))
    draw.polygon(tri_subject, fill=c_red)
    
    # Elegant borders on the triangle
    draw.line([(0, 1580), (850, 2120)], fill=(235, 65, 70), width=4)
    draw.line([(850, 2120), (0, 2660)], fill=(140, 10, 15), width=5)

    # Text inside the red triangle
    cx = 260
    tri_lines = [
        ("SUJET DU STAGE", f_tri_badge, (255, 255, 255)),
        ("─────────────────", f_tri_sub, (255, 190, 195)),
        ("Conception &", f_tri_main, (255, 255, 255)),
        ("Développement d'une", f_tri_main, (255, 255, 255)),
        ("Application Web", f_tri_bold, (255, 255, 255)),
        ("de Gestion des RH", f_tri_bold, (255, 255, 255)),
        ("& des Contrats", f_tri_bold, (255, 255, 255)),
        ("de Travail", f_tri_main, (255, 255, 255)),
    ]
    
    y_start = 1880
    for t_str, t_f, t_col in tri_lines:
        bb = draw.textbbox((0, 0), t_str, font=t_f)
        tw = bb[2] - bb[0]
        draw.text((cx - (tw // 2), y_start), t_str, font=t_f, fill=t_col)
        y_start += 54

    # 4. ESPRIT Logo (Centered around x=1550)
    logo_center_x = 1550
    logo_y = 130
    
    bbox_espr = draw.textbbox((0, 0), "espr", font=f_arial_b_huge)
    w_espr = bbox_espr[2] - bbox_espr[0]
    bbox_i = draw.textbbox((0, 0), "ı", font=f_arial_b_huge)
    w_i = bbox_i[2] - bbox_i[0]
    bbox_t = draw.textbbox((0, 0), "t", font=f_arial_b_huge)
    w_t = bbox_t[2] - bbox_t[0]
    
    total_logo_w = w_espr + w_i + w_t + 50
    start_lx = logo_center_x - (total_logo_w // 2)
    
    draw.text((start_lx, logo_y), "espr", font=f_arial_b_huge, fill=c_black)
    cur_x = start_lx + w_espr + 6
    
    # 'i' (dotless)
    draw.text((cur_x, logo_y + 36), "ı", font=f_arial_b_huge, fill=c_black)
    # Red triangle on the 'i'
    tri_i = [(cur_x + 14, logo_y + 10), (cur_x + 75, logo_y + 36), (cur_x + 14, logo_y + 62)]
    draw.polygon(tri_i, fill=c_red)
    cur_x += w_i + 34
    
    # 't'
    draw.text((cur_x, logo_y), "t", font=f_arial_b_huge, fill=(185, 188, 192))
    
    # Slogan centered
    slogan_text = "Se former autrement"
    bbox_slog = draw.textbbox((0, 0), slogan_text, font=f_slogan)
    w_slog = bbox_slog[2] - bbox_slog[0]
    draw.text((logo_center_x - (w_slog // 2), logo_y + 165), slogan_text, font=f_slogan, fill=c_black)

    # 5. Title: RAPPORT DE STAGE D'IMMERSION EN ENTREPRISE (Centered)
    title_y = 650
    t1 = "RAPPORT DE STAGE"
    t2 = "D'IMMERSION EN ENTREPRISE"
    b1 = draw.textbbox((0, 0), t1, font=f_arial_b_title)
    b2 = draw.textbbox((0, 0), t2, font=f_arial_b_title)
    draw.text((logo_center_x - ((b1[2]-b1[0]) // 2), title_y), t1, font=f_arial_b_title, fill=c_black)
    draw.text((logo_center_x - ((b2[2]-b2[0]) // 2), title_y + 110), t2, font=f_arial_b_title, fill=c_black)

    # 6. Red Banner Ribbon
    banner_y = 1000
    banner_h = 145
    draw.rectangle([0, banner_y, width, banner_y + banner_h], fill=c_dark_red)
    draw.line([(0, banner_y), (width, banner_y)], fill=(120, 10, 15), width=5)
    draw.line([(0, banner_y + banner_h), (width, banner_y + banner_h)], fill=(90, 6, 10), width=5)

    # 7. Information Fields (Shifted to x=920 to allow generous room for red triangle)
    fx = 920
    fy = 1420
    spacing = 230

    # Specialty
    draw.text((fx, fy), "SPÉCIALITÉ :", font=f_arial_b_field, fill=c_black)
    draw.text((fx + 500, fy - 8), "Informatique", font=f_arial_title, fill=c_black)

    # Realized by
    fy += spacing
    draw.text((fx, fy), "Réalisé par :", font=f_arial_b_field, fill=c_black)
    draw.text((fx + 460, fy + 4), "SAHLI Yakine Eddine", font=f_arial_field, fill=c_black)

    # Proposed by
    fy += spacing
    draw.text((fx, fy), "Proposé par :", font=f_arial_b_field, fill=c_black)
    draw.text((fx + 460, fy + 4), "CSI Digital  (Entreprise d'accueil)", font=f_arial_field, fill=c_black)

    # Supervised by (Mme Kharbech Rayen)
    fy += spacing
    draw.text((fx, fy), "Encadré par :", font=f_arial_b_field, fill=c_black)
    draw.text((fx + 460, fy + 4), "Mme Kharbech Rayen", font=f_arial_field, fill=c_black)

    # Stage Period
    fy += spacing
    draw.text((fx, fy), "Période :", font=f_arial_b_field, fill=c_black)
    draw.text((fx + 460, fy + 4), "03/08/2026 – 13/09/2026", font=f_arial_field, fill=c_black)

    # University Year (Bottom Right)
    draw.text((1200, 3150), "Année universitaire : 2025 – 2026", font=f_year, fill=c_black)

    im.save(output_path, "PNG", dpi=(300, 300))
    print(f"Cover image saved successfully to {output_path}")

if __name__ == "__main__":
    out = r"C:\Users\Home\.gemini\antigravity-ide\scratch\gestion-rh-app\cover_esprit_hd.png"
    create_esprit_cover(out)
