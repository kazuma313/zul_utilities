import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

class DynamicMarkdownToPPTXService:
    """
    Service dinamis untuk convert Markdown ke PPTX
    - Auto detect template (pakai template jika ada, generate baru jika tidak)
    - Customizable font styling per header level
    - Support image dari file path (no matplotlib execution)
    """
    
    def __init__(self, template_path=None, style_config=None):
        """
        Initialize service
        
        Args:
            template_path: Path ke template .pptx (optional)
            style_config: Dict untuk custom font styling (optional)
        """
        self.template_path = template_path
        self.use_template = False
        
        # Check template
        if template_path and Path(template_path).exists():
            self.prs = Presentation(template_path)
            self.use_template = True
            print(f"✅ Mode: Template-based (using {template_path})")
        else:
            self.prs = Presentation()
            self.prs.slide_width = Inches(10)
            self.prs.slide_height = Inches(5.625)
            print(f"✅ Mode: Generate from scratch")
            if template_path:
                print(f"   ⚠️  Template not found: {template_path}")
        
        # Set style configuration dengan merge
        self.style_config = self.get_default_style()
        if style_config:
            self._merge_style(style_config)
    
    def get_default_style(self):
        """Default styling configuration"""
        return {
            'h1': {
                'font_size': 44,
                'font_name': 'Calibri',
                'font_color': RGBColor(0, 51, 102),
                'bold': True,
                'italic': False,
            },
            'h2': {
                'font_size': 32,
                'font_name': 'Calibri',
                'font_color': RGBColor(230, 126, 34),
                'bold': True,
                'italic': False,
            },
            'h3': {
                'font_size': 24,
                'font_name': 'Calibri',
                'font_color': RGBColor(52, 73, 94),
                'bold': True,
                'italic': False,
            },
            'body': {
                'font_size': 14,
                'font_name': 'Calibri',
                'font_color': RGBColor(60, 60, 60),
                'bold': False,
                'italic': False,
            },
            'bullet': {
                'font_size': 16,
                'font_name': 'Calibri',
                'font_color': RGBColor(60, 60, 60),
                'bold': False,
                'italic': False,
            },
        }
    
    def _merge_style(self, new_style):
        """Deep merge new style dengan existing style"""
        for key, value in new_style.items():
            if key in self.style_config:
                self.style_config[key].update(value)
            else:
                self.style_config[key] = value
    
    def set_style(self, style_dict):
        """
        Update style configuration
        
        Example:
            service.set_style({
                'h1': {'font_size': 48, 'font_color': RGBColor(255, 0, 0)}
            })
        """
        self._merge_style(style_dict)
        print(f"✅ Style updated for: {', '.join(style_dict.keys())}")
    
    def apply_text_style(self, paragraph, style_type='body'):
        """Apply styling ke paragraph berdasarkan style type"""
        if style_type in self.style_config:
            style = self.style_config[style_type]
        else:
            style = self.style_config.get('body', {})
        
        if 'font_size' in style and style['font_size']:
            paragraph.font.size = Pt(style['font_size'])
        if 'font_name' in style and style['font_name']:
            paragraph.font.name = style['font_name']
        if 'font_color' in style and style['font_color']:
            paragraph.font.color.rgb = style['font_color']
        if 'bold' in style:
            paragraph.font.bold = style['bold']
        if 'italic' in style:
            paragraph.font.italic = style['italic']
    
    def create_blank_slide(self):
        """Create blank slide"""
        if self.use_template:
            try:
                blank_layout = self.prs.slide_layouts[6]
            except IndexError:
                blank_layout = self.prs.slide_layouts[-1]
            slide = self.prs.slides.add_slide(blank_layout)
        else:
            blank_layout = self.prs.slide_layouts[6]
            slide = self.prs.slides.add_slide(blank_layout)
            
            # Remove all shapes
            for shape in list(slide.shapes):
                sp = shape.element
                sp.getparent().remove(sp)
            
            # Set background
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor(255, 255, 255)
        
        return slide
    
    def add_styled_textbox(self, slide, text, left, top, width, height, style_type='body'):
        """Add textbox dengan custom styling"""
        textbox = slide.shapes.add_textbox(
            Inches(left), 
            Inches(top), 
            Inches(width), 
            Inches(height)
        )
        
        text_frame = textbox.text_frame
        text_frame.word_wrap = True
        text_frame.clear()
        
        p = text_frame.add_paragraph()
        p.text = text
        p.alignment = PP_ALIGN.LEFT
        
        self.apply_text_style(p, style_type)
        
        return textbox
    
    def add_bullet_textbox(self, slide, bullets, left, top, width, style_type='bullet'):
        """Add textbox dengan bullet points"""
        total_height = len(bullets) * 0.35 + 0.2
        
        textbox = slide.shapes.add_textbox(
            Inches(left),
            Inches(top),
            Inches(width),
            Inches(total_height)
        )
        
        text_frame = textbox.text_frame
        text_frame.word_wrap = True
        text_frame.clear()
        
        for bullet_text in bullets:
            p = text_frame.add_paragraph()
            p.text = bullet_text
            p.level = 0
            self.apply_text_style(p, style_type)
        
        return total_height
    
    def add_image(self, slide, image_path, left=1.5, top=3, width=7, height=None):
        """
        Add image ke slide dari file path
        
        Args:
            slide: Slide object
            image_path: Path ke image file
            left, top: Position dalam inches
            width: Width dalam inches
            height: Height dalam inches (optional, auto jika None)
        
        Returns:
            Picture shape atau None jika gagal
        """
        if not Path(image_path).exists():
            print(f"⚠️  Image not found: {image_path}")
            return None
        
        try:
            if height:
                pic = slide.shapes.add_picture(
                    image_path,
                    Inches(left),
                    Inches(top),
                    width=Inches(width),
                    height=Inches(height)
                )
            else:
                pic = slide.shapes.add_picture(
                    image_path,
                    Inches(left),
                    Inches(top),
                    width=Inches(width)
                )
            return pic
        except Exception as e:
            print(f"⚠️  Error adding image: {e}")
            return None
    
    def fill_template_placeholder(self, slide, title=None, content=None):
        """Fill placeholder di template slide"""
        for shape in slide.placeholders:
            ph_type = shape.placeholder_format.type
            
            # Title placeholder
            if ph_type == 1 and title:
                shape.text = title
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        if paragraph.text:
                            self.apply_text_style(paragraph, 'h2')
            
            # Body/Content placeholder
            elif ph_type in [2, 7] and content:
                if not shape.has_text_frame:
                    continue
                
                text_frame = shape.text_frame
                text_frame.clear()
                
                if isinstance(content, list):
                    for item in content:
                        p = text_frame.add_paragraph()
                        p.text = str(item)
                        p.level = 0
                        self.apply_text_style(p, 'bullet')
                else:
                    p = text_frame.add_paragraph()
                    p.text = str(content)
                    self.apply_text_style(p, 'body')
    
    def add_slide_from_content(self, title=None, content=None, image_paths=None, layout_index=1):
        """
        Add slide dengan content
        
        Args:
            title: Slide title
            content: String atau list untuk content
            image_paths: List of image paths atau single path
            layout_index: Layout index jika pakai template
        """
        if self.use_template:
            # Mode template: gunakan layout dan fill placeholder
            try:
                layout = self.prs.slide_layouts[layout_index]
            except IndexError:
                layout = self.prs.slide_layouts[1]
            
            slide = self.prs.slides.add_slide(layout)
            self.fill_template_placeholder(slide, title, content)
        
        else:
            # Mode generate: buat manual dengan positioning
            slide = self.create_blank_slide()
            
            current_y = 0.5
            
            # Add title
            if title:
                self.add_styled_textbox(slide, title, 0.5, current_y, 9, 0.8, 'h2')
                current_y += 1
            
            # Add content
            if content:
                if isinstance(content, list):
                    height = self.add_bullet_textbox(slide, content, 0.8, current_y, 8.5, 'bullet')
                    current_y += height + 0.3
                else:
                    self.add_styled_textbox(slide, content, 0.5, current_y, 9, 0.6, 'body')
                    current_y += 0.8
        
        # Add images
        if image_paths:
            paths = image_paths if isinstance(image_paths, list) else [image_paths]
            
            for img_path in paths:
                if img_path:
                    pic = self.add_image(
                        slide, 
                        img_path,
                        left=1.5,
                        top=3 if self.use_template else current_y, # type: ignore
                        width=7
                    )
                    if pic and not self.use_template:
                        current_y += pic.height.inches + 0.2 # type: ignore
        
        return slide
    
    def convert_markdown(self, md_content, output_path):
        """
        Convert markdown ke PPTX
        
        Supported syntax:
        - # Heading 1 (title)
        - ## Heading 2 (subtitle/section)
        - ### Heading 3 (sub-section)
        - * Bullet point
        - ![alt text](path/to/image.png) - untuk add image
        - --- untuk slide separator
        
        Args:
            md_content: String markdown content
            output_path: Output file path
        """
        # Split by slide separator
        slides_content = md_content.split('\n---\n')
        
        for idx, slide_content in enumerate(slides_content):
            if not slide_content.strip():
                continue
            
            lines = [l for l in slide_content.split('\n') if l.strip()]
            
            title = None
            content_items = []
            image_paths = []
            
            for line in lines:
                line = line.strip()
                
                # Header level 1 (# Header)
                if line.startswith('# '):
                    title = line.replace('# ', '').strip()
                
                # Header level 2 (## Header)
                elif line.startswith('## '):
                    heading = line.replace('## ', '').strip()
                    if not title:
                        title = heading
                    else:
                        content_items.append(heading)
                
                # Header level 3 (### Header)
                elif line.startswith('### '):
                    content_items.append(line.replace('### ', '').strip())
                
                # Bullet point
                elif line.startswith('* ') or line.startswith('- '):
                    bullet_text = line.lstrip('*- ').strip()
                    content_items.append(bullet_text)
                
                # Image reference ![alt](path)
                elif line.startswith('!['):
                    match = re.match(r'!\[.*?\]\((.*?)\)', line)
                    if match:
                        image_paths.append(match.group(1))
                
                # Regular text
                elif line:
                    content_items.append(line)
            
            # Add slide
            content = content_items if content_items else None
            self.add_slide_from_content(
                title=title,
                content=content,
                image_paths=image_paths if image_paths else None,
                layout_index=1
            )
        
        # Save
        self.prs.save(output_path)
        mode = "template-based" if self.use_template else "generated"
        print(f"\n✅ Presentasi berhasil dibuat ({mode}): {output_path}")
        print(f"   Total slides: {len(self.prs.slides)}")
    
    def save(self, output_path):
        """Save presentation"""
        self.prs.save(output_path)
        print(f"✅ Saved: {output_path}")




# # ============ CONTOH PENGGUNAAN ============

# def example_with_template():
#     """Contoh pakai template"""
    
#     # Custom font styling
#     custom_style = {
#         'h2': {
#             'font_size': 36,
#             'font_color': RGBColor(0, 102, 204),
#             'bold': True,
#         },
#         'bullet': {
#             'font_size': 18,
#         }
#     }
    
#     service = DynamicMarkdownToPPTXService(
#         template_path='data/ppt/template.pptx',
#         style_config=custom_style
#     )
    
#     markdown_content = """
# # Judul Presentasi PLN

# ---

# ## Topik 1 - Overview

# * Point pertama tentang sistem
# * Point kedua tentang infrastruktur
# * Point ketiga tentang target

# ---

# ## Topik 2 - Data Visualization

# Berikut adalah grafik performa:

# ![Chart Performance](data/images/chart1.png)

# ---

# ## Topik 3 - Multiple Images

# * Grafik A
# * Grafik B

# ![Chart A](data/images/chart_a.png)
# ![Chart B](data/images/chart_b.png)

# ---

# ## Kesimpulan

# * Target tercapai
# * Efisiensi meningkat
# * Rekomendasi untuk tahun depan
# """
    
#     service.convert_markdown(markdown_content, 'output_template.pptx')


# def example_without_template():
#     """Contoh tanpa template (generate from scratch)"""
    
#     service = DynamicMarkdownToPPTXService(
#         template_path=None
#     )
    
#     markdown_content = """
# # Welcome Presentation

# ---

# ## Introduction

# * Feature 1
# * Feature 2
# * Feature 3

# ---

# ## Data Section

# Hasil analisis data:

# ![Data Chart](data/images/analysis.png)
# """
    
#     service.convert_markdown(markdown_content, 'output_generated.pptx')


# def example_manual_slide_creation():
#     """Contoh create slide manual (bukan dari markdown)"""
    
#     service = DynamicMarkdownToPPTXService(
#         template_path='data/ppt/template.pptx'
#     )
    
#     # Add slide 1
#     service.add_slide_from_content(
#         title='Slide 1',
#         content=['Point A', 'Point B', 'Point C']
#     )
    
#     # Add slide 2 dengan image
#     service.add_slide_from_content(
#         title='Slide 2 - Chart',
#         content=['Grafik performance', 'Trend meningkat'],
#         image_paths='data/images/chart.png'
#     )
    
#     # Add slide 3 dengan multiple images
#     service.add_slide_from_content(
#         title='Slide 3 - Multiple Charts',
#         content=None,
#         image_paths=['data/images/chart1.png', 'data/images/chart2.png']
#     )
    
#     service.save('output_manual.pptx')


# if __name__ == '__main__':
#     example_with_template()
#     example_without_template()
#     example_manual_slide_creation()
